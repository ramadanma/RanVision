"""Per-source detection worker thread."""
import asyncio
import logging
import threading
import time
from contextlib import asynccontextmanager

import cv2
import numpy as np

from app.worker import insightface_stub, yolo_stub
from app.worker.rule_engine import rule_engine

logger = logging.getLogger(__name__)

CONFIG_RELOAD_INTERVAL = 5.0     # seconds between zone/face reloads
FACE_RELOAD_INTERVAL = 60.0      # seconds between face embedding reloads
PHOTO_MAX_FRAMES = 300           # max frames cached per track in Redis
PHOTO_TTL = 300                  # seconds


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

        from app.config import settings
        self._device = source_id % max(settings.GPU_COUNT, 1)

    def stop(self) -> None:
        self._stop_event.set()

    # ── Zone reload ──────────────────────────────────────────────────────────

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
            self._zones = asyncio.run(_fetch())
            total_rules = sum(len(z.rules) for z in self._zones)
            logger.info("Source %d: loaded %d zone(s) with %d rule(s)", self.source_id, len(self._zones), total_rules)
        except Exception as e:
            logger.warning("Zone reload failed for source %d: %s", self.source_id, e)

    # ── Face embedding reload ─────────────────────────────────────────────────

    def _reload_faces(self) -> None:
        try:
            from app.services.face_service import load_embeddings_for_user
            self._known_faces = load_embeddings_for_user(self.user_id)
            logger.debug("Loaded %d face embeddings for user %d", len(self._known_faces), self.user_id)
        except Exception as e:
            logger.warning("Face reload failed: %s", e)

    # ── Direct source URL ────────────────────────────────────────────────────

    def _get_capture_url(self) -> str | None:
        """Load source from DB and return direct capture URL (RTSP or file path)."""
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
            return asyncio.run(_fetch())
        except Exception as e:
            logger.error("Failed to get capture URL for source %d: %s", self.source_id, e)
            return None

    # ── Main loop ─────────────────────────────────────────────────────────────

    # Push every Nth frame to keep WebSocket ~10 fps regardless of source fps
    _PUSH_EVERY_N = 3

    def run(self) -> None:
        logger.info("StreamProcessor started for source %d (device=cuda:%d)", self.source_id, self._device)
        url = self._get_capture_url()
        if not url:
            logger.error("Cannot resolve capture URL for source %d, worker exiting", self.source_id)
            return

        logger.info("StreamProcessor source %d opening: %s", self.source_id, url)
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            logger.error("Cannot open video for source %d (url=%s)", self.source_id, url)
            return
        logger.info("StreamProcessor source %d capture opened successfully", self.source_id)

        from app.services.frame_buffer import frame_buffer
        frame_count = 0
        fail_count = 0

        try:
            while not self._stop_event.is_set():
                now = time.time()

                if now - self._last_reload > CONFIG_RELOAD_INTERVAL:
                    self._reload_zones()
                    self._last_reload = now

                if now - self._last_face_reload > FACE_RELOAD_INTERVAL:
                    self._reload_faces()
                    self._last_face_reload = now

                ret, frame = cap.read()
                if not ret:
                    fail_count += 1
                    if fail_count >= 10:
                        # EOF or stream drop — reopen
                        logger.info("Reopening capture for source %d (EOF/disconnect after %d fails)", self.source_id, fail_count)
                        cap.release()
                        time.sleep(1)
                        cap = cv2.VideoCapture(url)
                        fail_count = 0
                    else:
                        time.sleep(0.1)
                    continue
                fail_count = 0
                frame_count += 1

                # Push every Nth frame to WebSocket buffer
                if frame_count % self._PUSH_EVERY_N == 0:
                    _, jpeg_buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    frame_buffer.push(self.source_id, jpeg_buf.tobytes())
                    if frame_count == self._PUSH_EVERY_N:
                        logger.info("First frame pushed to buffer for source %d", self.source_id)

                if frame_count % 150 == 0:
                    logger.info("StreamProcessor source %d alive: %d frames processed", self.source_id, frame_count)

                detections = yolo_stub.infer(frame, device=self._device)
                identities = insightface_stub.identify(frame, detections, self._known_faces)

                # Push frame to Redis for each tracked person in any zone
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
            cap.release()
            frame_buffer.clear(self.source_id)
            logger.info("StreamProcessor stopped for source %d", self.source_id)

    # ── Photo caching ─────────────────────────────────────────────────────────

    def _cache_photos(self, frame: np.ndarray, detections: list[dict]) -> None:
        if not detections or not self._zones:
            return
        # Only cache for detections that are inside at least one zone
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
            asyncio.run(_push())
        except Exception as e:
            logger.debug("Photo cache error: %s", e)

    # ── Trigger handler ───────────────────────────────────────────────────────

    def _on_trigger(self, event: dict) -> None:
        import json
        logger.info(
            "Rule triggered: source=%d rule=%d zone=%d track=%d snapshot=%s",
            self.source_id, event["rule_id"], event["zone_id"],
            event["track_id"], event.get("snapshot"),
        )

        async def _handle():
            from app.models.trigger_record import TriggerRecord
            from app.models.report_config import ReportConfig
            from app.services.alert_service import _select_photos, send_alert
            from app.services.smtp_config_service import get_smtp_config_dict
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            async with _thread_db() as db:
                # Always save a TriggerRecord — independent of report configs
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

                # Alert delivery — only for matching enabled report configs
                result = await db.execute(
                    select(ReportConfig)
                    .where(ReportConfig.source_id == self.source_id, ReportConfig.is_enabled == True)
                    .options(selectinload(ReportConfig.trigger_rules))
                )
                configs = list(result.scalars().all())
                smtp_cfg = await get_smtp_config_dict(db)

                for config in configs:
                    rule_ids = [r.id for r in config.trigger_rules]
                    if event["rule_id"] not in rule_ids:
                        continue

                    photos: list[bytes] = []
                    if config.photo_count > 0:
                        from app.services.redis_service import get_redis
                        redis = await get_redis()
                        key = f"photo:{self.source_id}:{event['track_id']}"
                        raw_frames = await redis.lrange(key, 0, -1)
                        photos = _select_photos(raw_frames, config.photo_count)
                        await redis.delete(key)

                    person_name = event.get("person_name") if config.include_person_name else None
                    subject = f"[RanVision] 规则触发: #{event['rule_id']}"
                    body = (
                        f"Source: {self.source_id}\nZone: {event['zone_id']}\n"
                        f"Rule: {event['rule_id']}\n"
                        + (f"Person: {person_name}\n" if person_name else "")
                        + f"Details: {json.dumps(event.get('snapshot', {}), ensure_ascii=False)}"
                    )

                    delivered = False
                    delivery_error = None
                    try:
                        await send_alert(config.delivery_method, config.destination, subject, body, photos, smtp_cfg=smtp_cfg)
                        delivered = True
                    except Exception as e:
                        delivery_error = str(e)[:500]
                        logger.error("Alert send failed for source %d: %s", self.source_id, e)

                    record.photos_sent = len(photos)
                    record.alert_delivered = delivered
                    record.delivery_error = delivery_error
                    await db.commit()

        try:
            asyncio.run(_handle())
        except Exception as e:
            logger.error("Trigger handler error for source %d: %s", self.source_id, e)
