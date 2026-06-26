"""Per-source detection worker thread.

Three-thread architecture:
  reader thread   — cap.read() + frame_buffer push (never blocked by GPU)
  inference thread (main) — YOLO + face + rule evaluation
  trigger thread  — DB write + alert delivery (never blocks inference)
"""
import asyncio
import logging
import queue
import threading
import time
from contextlib import asynccontextmanager

import cv2
import numpy as np

from app.worker import insightface_stub, yolo_stub
from app.worker.rule_engine import rule_engine

logger = logging.getLogger(__name__)


def _render_template(template: str, context: dict) -> str:
    """Replace {{variable}} placeholders with values from context."""
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template


CONFIG_RELOAD_INTERVAL = 5.0     # seconds between zone/face reloads
FACE_RELOAD_INTERVAL = 60.0      # seconds between face embedding reloads
PHOTO_MAX_FRAMES = 300           # max frames cached per track in Redis
PHOTO_TTL = 300                  # seconds

# COCO 17-keypoint skeleton connections
COCO_SKELETON = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6),
    (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16),
]


@asynccontextmanager
async def _thread_db():
    """Fresh DB session for background thread — avoids event-loop conflicts."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from app.config import settings
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with Session() as session:
            yield session
    finally:
        await engine.dispose()


class StreamProcessor(threading.Thread):
    def __init__(self, source_id: int, user_id: int = 0):
        super().__init__(name=f"worker-{source_id}", daemon=True)
        self.source_id = source_id
        self.user_id = user_id
        self._stop_event = threading.Event()
        self._zones: list = []
        self._known_faces: list[tuple[str, np.ndarray]] = []
        self._last_reload = 0.0
        self._last_face_reload = 0.0
        self._loop: asyncio.AbstractEventLoop | None = None
        self._active_track_ids: set[int] = set()
        self._face_recognition_enabled: bool = True
        self._face_check_front: bool = False
        self._show_skeleton: bool = False
        self._detection_roi: np.ndarray | None = None

        # Latest detections — written by inference thread, read by reader thread (GIL-safe)
        self._prev_detections: list = []
        # Set by reader thread on reconnect; cleared by inference thread after cleanup
        self._reconnect_signal: bool = False

        # Frame queue: reader → inference (bounded; drop stale frames on full)
        self._infer_q: queue.Queue = queue.Queue(maxsize=2)
        # Trigger queue: inference → I/O worker (unbounded — never drop events)
        self._trigger_q: queue.Queue = queue.Queue()

        from app.config import settings
        self._device = source_id % max(settings.GPU_COUNT, 1)

    def stop(self) -> None:
        self._stop_event.set()

    def _run_async(self, coro):
        """Run a coroutine on this thread's persistent event loop."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)

    # ── Zone / source-flag / face reload (called from inference thread) ───────

    def _reload_zones(self) -> None:
        from app.models.zone import Zone
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async def _fetch():
            async with _thread_db() as db:
                result = await db.execute(
                    select(Zone)
                    .where(Zone.source_id == self.source_id)
                    .options(selectinload(Zone.rules))
                )
                return list(result.scalars().all())

        try:
            self._zones = self._run_async(_fetch())
            total_rules = sum(len(z.rules) for z in self._zones)
            logger.info("Source %d: loaded %d zone(s) with %d rule(s)", self.source_id, len(self._zones), total_rules)
        except Exception as e:
            logger.warning("Zone reload failed for source %d: %s", self.source_id, e)

    def _reload_source_flags(self) -> None:
        async def _fetch():
            from sqlalchemy import select
            from app.models.source import Source
            async with _thread_db() as db:
                result = await db.execute(select(Source).where(Source.id == self.source_id))
                source = result.scalar_one_or_none()
                if source:
                    return (
                        source.face_recognition_enabled,
                        source.face_check_front,
                        source.show_skeleton,
                        source.detection_roi_json,
                    )
                return True, False, False, None

        try:
            enabled, check_front, show_skeleton, roi_json = self._run_async(_fetch())
            self._face_recognition_enabled = enabled
            self._face_check_front = check_front
            self._show_skeleton = show_skeleton
            if roi_json:
                import json
                self._detection_roi = np.array(json.loads(roi_json), dtype=np.float32)
            else:
                self._detection_roi = None
        except Exception as e:
            logger.warning("Source flags reload failed for source %d: %s", self.source_id, e)

    def _reload_faces(self) -> None:
        async def _fetch():
            from sqlalchemy import select
            from app.models.face import Face
            async with _thread_db() as db:
                result = await db.execute(
                    select(Face).where(
                        Face.user_id == self.user_id,
                        Face.embedding_path.isnot(None),
                    )
                )
                pairs = []
                for face in result.scalars().all():
                    try:
                        emb = np.load(face.embedding_path)
                        pairs.append((face.person_name, emb))
                    except Exception as load_err:
                        logger.warning("Failed to load embedding for face %s: %s", face.person_name, load_err)
                return pairs

        try:
            self._known_faces = self._run_async(_fetch())
            logger.info("Loaded %d face embedding(s) for user %d", len(self._known_faces), self.user_id)
        except Exception as e:
            logger.warning("Face reload failed for user %d: %s", self.user_id, e)

    # ── ROI filter ────────────────────────────────────────────────────────────

    def _filter_by_roi(self, detections: list[dict], frame_shape: tuple) -> list[dict]:
        if self._detection_roi is None or len(detections) == 0:
            return detections
        h, w = frame_shape[:2]
        roi_px = (self._detection_roi * np.array([w, h])).astype(np.int32)
        filtered = []
        for det in detections:
            bbox = det["bbox"]
            cx = int((bbox[0] + bbox[2]) / 2)
            cy = int((bbox[1] + bbox[3]) / 2)
            if cv2.pointPolygonTest(roi_px, (float(cx), float(cy)), False) >= 0:
                filtered.append(det)
        return filtered

    # ── Skeleton draw ─────────────────────────────────────────────────────────

    def _draw_skeleton(self, frame: np.ndarray, detections: list[dict]) -> None:
        for det in detections:
            kps = det.get("keypoints", [])
            if len(kps) < 17:
                continue
            for a, b in COCO_SKELETON:
                if kps[a][2] > 0.3 and kps[b][2] > 0.3:
                    cv2.line(frame,
                             (int(kps[a][0]), int(kps[a][1])),
                             (int(kps[b][0]), int(kps[b][1])),
                             (0, 255, 0), 2)
            for kp in kps:
                if kp[2] > 0.3:
                    cv2.circle(frame, (int(kp[0]), int(kp[1])), 3, (0, 255, 255), -1)

    # ── Direct source URL ────────────────────────────────────────────────────

    def _get_capture_url(self) -> str | None:
        async def _fetch():
            from sqlalchemy import select
            from app.models.source import Source
            async with _thread_db() as db:
                result = await db.execute(select(Source).where(Source.id == self.source_id))
                source = result.scalar_one_or_none()
                if not source:
                    return None
                if source.source_type == "file":
                    return source.file_path
                from app.services.source_service import build_rtsp_url
                return build_rtsp_url(source)
        try:
            return self._run_async(_fetch())
        except Exception as e:
            logger.error("Failed to get capture URL for source %d: %s", self.source_id, e)
            return None

    # ── Reader thread ─────────────────────────────────────────────────────────

    _PUSH_EVERY_N = 2  # keep WebSocket display ~15 fps on a 30fps source

    def _reader_loop(self, url: str) -> None:
        """Dedicated read thread: cap.read() + display push + enqueue for inference.

        Completely decoupled from GPU speed so display latency is never gated
        by YOLO inference time.  Uses a bounded queue with drop-on-full so the
        inference thread always works on a recent frame, not a stale backlog.
        """
        from app.services.frame_buffer import frame_buffer

        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            logger.error("Reader: cannot open video for source %d (url=%s)", self.source_id, url)
            self._stop_event.set()
            return
        logger.info("Reader: capture opened for source %d", self.source_id)

        frame_count = 0
        fail_count = 0

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    fail_count += 1
                    if fail_count >= 10:
                        logger.info("Reader: reopening capture for source %d", self.source_id)
                        cap.release()
                        time.sleep(1)
                        cap = cv2.VideoCapture(url)
                        # Signal inference thread to reset tracker + clean Redis
                        self._reconnect_signal = True
                        self._prev_detections = []
                        fail_count = 0
                    else:
                        time.sleep(0.05)
                    continue
                fail_count = 0
                frame_count += 1

                # Push to display buffer — skeleton overlay uses latest inference results
                if frame_count % self._PUSH_EVERY_N == 0:
                    prev = list(self._prev_detections)
                    if self._show_skeleton and prev:
                        display = frame.copy()
                        self._draw_skeleton(display, prev)
                    else:
                        display = frame
                    _, jpeg_buf = cv2.imencode(".jpg", display, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    frame_buffer.push(self.source_id, jpeg_buf.tobytes())
                    if frame_count == self._PUSH_EVERY_N:
                        logger.info("Reader: first frame pushed for source %d", self.source_id)

                # Drop stale frame if inference is falling behind
                if self._infer_q.full():
                    try:
                        self._infer_q.get_nowait()
                    except queue.Empty:
                        pass
                try:
                    self._infer_q.put_nowait(frame)
                except queue.Full:
                    pass
        finally:
            cap.release()
            frame_buffer.clear(self.source_id)
            logger.info("Reader: stopped for source %d", self.source_id)

    # ── Trigger I/O worker thread ─────────────────────────────────────────────

    def _trigger_worker_loop(self) -> None:
        """Dedicated I/O thread: handles DB writes and alert delivery per trigger event.

        Runs on its own event loop and its own Redis client so it never blocks
        the inference thread and avoids event-loop conflicts with the inference
        thread's _run_async loop.
        """
        import redis.asyncio as aioredis
        from app.config import settings

        io_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(io_loop)

        async def _run() -> None:
            redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
            try:
                while not self._stop_event.is_set() or not self._trigger_q.empty():
                    try:
                        event = self._trigger_q.get_nowait()
                    except queue.Empty:
                        await asyncio.sleep(0.1)
                        continue
                    try:
                        await self._handle_trigger(event, redis_client)
                    except Exception as e:
                        logger.error("Trigger I/O error for source %d: %s", self.source_id, e)
                    finally:
                        self._trigger_q.task_done()
            finally:
                await redis_client.aclose()

        try:
            io_loop.run_until_complete(_run())
        finally:
            io_loop.close()
            logger.info("Trigger worker stopped for source %d", self.source_id)

    # ── Main loop (inference) ─────────────────────────────────────────────────

    def run(self) -> None:
        logger.info("StreamProcessor started for source %d (device=cuda:%d)", self.source_id, self._device)
        url = self._get_capture_url()
        if not url:
            logger.error("Cannot resolve capture URL for source %d, worker exiting", self.source_id)
            return

        reader_t = threading.Thread(
            target=self._reader_loop, args=(url,),
            name=f"reader-{self.source_id}", daemon=True,
        )
        reader_t.start()

        trigger_t = threading.Thread(
            target=self._trigger_worker_loop,
            name=f"trigger-{self.source_id}", daemon=True,
        )
        trigger_t.start()

        frame_count = 0
        try:
            while not self._stop_event.is_set():
                now = time.time()

                if now - self._last_reload > CONFIG_RELOAD_INTERVAL:
                    self._reload_zones()
                    self._reload_source_flags()
                    self._last_reload = now

                if now - self._last_face_reload > FACE_RELOAD_INTERVAL:
                    self._reload_faces()
                    self._last_face_reload = now

                # Handle stream reconnect signaled by reader thread
                if self._reconnect_signal:
                    yolo_stub.reset_tracker(self._device)
                    self._delete_photo_keys(self._active_track_ids)
                    self._active_track_ids.clear()
                    self._reconnect_signal = False

                try:
                    frame = self._infer_q.get(timeout=1.0)
                except queue.Empty:
                    continue

                frame_count += 1
                detections = yolo_stub.infer(frame, device=self._device)
                detections = self._filter_by_roi(detections, frame.shape)
                self._prev_detections = detections  # reader thread picks this up

                if self._face_recognition_enabled and self._known_faces:
                    identities = insightface_stub.identify(
                        frame, detections, self._known_faces,
                        check_front_facing=self._face_check_front,
                    )
                else:
                    identities = {d["track_id"]: None for d in detections}

                current_ids = {d["track_id"] for d in detections}
                gone_ids = self._active_track_ids - current_ids
                if gone_ids:
                    self._delete_photo_keys(gone_ids)
                self._active_track_ids = current_ids

                if frame_count % 150 == 0:
                    logger.info(
                        "StreamProcessor source %d alive: %d frames inferred, %d person(s) detected",
                        self.source_id, frame_count, len(detections),
                    )

                self._cache_photos(frame, detections)

                rule_engine.evaluate(
                    frame=frame,
                    zones=self._zones,
                    detections=detections,
                    identities=identities,
                    source_id=self.source_id,
                    on_trigger_callback=self._on_trigger,
                )
        finally:
            self._stop_event.set()
            reader_t.join(timeout=5)
            self._trigger_q.join()  # wait for any pending alert deliveries
            trigger_t.join(timeout=10)
            if self._loop and not self._loop.is_closed():
                self._loop.close()
            logger.info("StreamProcessor stopped for source %d", self.source_id)

    # ── Photo key cleanup ────────────────────────────────────────────────────

    def _delete_photo_keys(self, track_ids: set[int]) -> None:
        if not track_ids:
            return

        async def _del():
            from app.services.redis_service import get_redis
            redis = await get_redis()
            keys = [f"photo:{self.source_id}:{tid}" for tid in track_ids]
            await redis.delete(*keys)

        try:
            self._run_async(_del())
        except Exception as e:
            logger.debug("Photo key cleanup error: %s", e)

    # ── Photo caching ─────────────────────────────────────────────────────────

    def _cache_photos(self, frame: np.ndarray, detections: list[dict]) -> None:
        if not detections or not self._zones:
            return
        in_zone_ids = set()
        for det in detections:
            for zone in self._zones:
                try:
                    from app.worker.rule_engine import rule_engine as re
                    import json
                    if zone.npy_path and __import__("os").path.exists(zone.npy_path):
                        poly_norm = np.load(zone.npy_path)
                    else:
                        poly_norm = np.array(json.loads(zone.polygon_json), dtype=np.float32)
                    h, w = frame.shape[:2]
                    polygon = (poly_norm * np.array([w, h])).astype(np.int32)
                    if re._person_in_zone(det, polygon, frame):
                        in_zone_ids.add(det["track_id"])
                except Exception:
                    pass

        if not in_zone_ids:
            return

        _, jpeg_bytes = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        jpeg = jpeg_bytes.tobytes()

        async def _push():
            from app.services.redis_service import get_redis
            redis = await get_redis()
            for tid in in_zone_ids:
                key = f"photo:{self.source_id}:{tid}"
                await redis.lpush(key, jpeg)
                await redis.ltrim(key, 0, PHOTO_MAX_FRAMES - 1)
                await redis.expire(key, PHOTO_TTL)

        try:
            self._run_async(_push())
        except Exception as e:
            logger.debug("Photo cache error: %s", e)

    # ── Trigger handler ───────────────────────────────────────────────────────

    def _on_trigger(self, event: dict) -> None:
        """Called from inference thread — enqueues event; returns immediately."""
        logger.info(
            "Rule triggered: source=%d rule=%d zone=%d track=%d snapshot=%s",
            self.source_id, event["rule_id"], event["zone_id"],
            event["track_id"], event.get("snapshot"),
        )
        self._trigger_q.put(event)

    async def _handle_trigger(self, event: dict, redis_client) -> None:
        """DB write + alert delivery — runs on the trigger worker's event loop."""
        import json
        from app.models.trigger_record import TriggerRecord
        from app.models.report_config import ReportConfig
        from app.services.alert_service import _select_photos, send_alert
        from app.services.smtp_config_service import get_smtp_config_dict
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with _thread_db() as db:
            record = TriggerRecord(
                source_id=self.source_id,
                rule_id=event["rule_id"],
                zone_id=event["zone_id"],
                person_name=event.get("person_name"),
                rule_snapshot_json=json.dumps(event.get("snapshot", {})),
                photos_sent=0,
                alert_delivered=False,
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            logger.info("TriggerRecord #%d saved for source %d", record.id, self.source_id)

            result = await db.execute(
                select(ReportConfig)
                .where(ReportConfig.source_id == self.source_id, ReportConfig.is_enabled == True)
                .options(selectinload(ReportConfig.trigger_rules))
            )
            configs = list(result.scalars().all())

            matched_any = False
            for config in configs:
                rule_ids = [r.id for r in config.trigger_rules]
                if event["rule_id"] not in rule_ids:
                    continue
                matched_any = True

                photos: list[bytes] = []
                delivered = False
                delivery_error = None
                try:
                    if config.photo_count > 0:
                        key = f"photo:{self.source_id}:{event['track_id']}"
                        raw_frames = await redis_client.lrange(key, 0, -1)
                        photos = _select_photos(raw_frames, config.photo_count)
                        await redis_client.delete(key)

                    person_name = event.get("person_name") if config.include_person_name else None
                    tpl_ctx = {
                        "source_id": str(self.source_id),
                        "zone_id": str(event["zone_id"]),
                        "rule_id": str(event["rule_id"]),
                        "person_name": person_name or "",
                        "triggered_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "details": json.dumps(event.get("snapshot", {}), ensure_ascii=False),
                    }
                    default_subject = f"[RanVision] 规则触发: #{event['rule_id']}"
                    default_body = (
                        f"Source: {self.source_id}\nZone: {event['zone_id']}\n"
                        f"Rule: {event['rule_id']}\n"
                        + (f"Person: {person_name}\n" if person_name else "")
                        + f"Details: {json.dumps(event.get('snapshot', {}), ensure_ascii=False)}"
                    )
                    subject = _render_template(config.subject_template, tpl_ctx) if config.subject_template else default_subject
                    body = _render_template(config.body_template, tpl_ctx) if config.body_template else default_body

                    smtp_cfg = await get_smtp_config_dict(db) if config.delivery_method == "email" else {}
                    await send_alert(config.delivery_method, config.destination, subject, body, photos, smtp_cfg=smtp_cfg)
                    delivered = True
                except Exception as e:
                    delivery_error = str(e)[:500]
                    logger.error("Alert send failed for config %d source %d: %s", config.id, self.source_id, e)

                record.photos_sent = len(photos)
                record.alert_delivered = delivered
                record.delivery_error = delivery_error
                await db.commit()

            if not matched_any:
                logger.info(
                    "Rule %d fired for source %d but no report config has this rule linked",
                    event["rule_id"], self.source_id,
                )
