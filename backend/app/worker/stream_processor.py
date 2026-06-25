"""Per-source detection worker thread."""
import logging
import threading
import time
from contextlib import asynccontextmanager

import cv2

from app.worker import insightface_stub, yolo_stub
from app.worker.rule_engine import rule_engine

logger = logging.getLogger(__name__)

CONFIG_RELOAD_INTERVAL = 5.0


@asynccontextmanager
async def _thread_db():
    """Create a fresh DB session for background thread use (avoids event-loop conflicts)."""
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
    def __init__(self, source_id: int):
        super().__init__(name=f"worker-{source_id}", daemon=True)
        self.source_id = source_id
        self._stop_event = threading.Event()
        self._zones: list = []
        self._last_reload = 0.0

    def stop(self) -> None:
        self._stop_event.set()

    def _reload_zones(self) -> None:
        from app.models.zone import Zone
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        import asyncio

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
        except Exception as e:
            logger.warning("Zone reload failed for source %d: %s", self.source_id, e)

    def _get_video_url(self) -> str | None:
        from app.config import settings
        import os
        manifest = os.path.join(settings.HLS_SEGMENTS_DIR, str(self.source_id), "index.m3u8")
        for _ in range(30):
            if os.path.exists(manifest):
                return manifest
            time.sleep(0.5)
        return None

    def run(self) -> None:
        logger.info("StreamProcessor started for source %d", self.source_id)
        url = self._get_video_url()
        if not url:
            logger.error("HLS manifest not found for source %d, worker exiting", self.source_id)
            return

        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            logger.error("Cannot open video for source %d", self.source_id)
            return

        try:
            while not self._stop_event.is_set():
                now = time.time()
                if now - self._last_reload > CONFIG_RELOAD_INTERVAL:
                    self._reload_zones()
                    self._last_reload = now

                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                detections = yolo_stub.infer(frame)
                identities = insightface_stub.identify(frame, detections)

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
            logger.info("StreamProcessor stopped for source %d", self.source_id)

    def _on_trigger(self, event: dict) -> None:
        import asyncio
        import json

        async def _handle():
            from app.models.trigger_record import TriggerRecord
            from app.models.report_config import ReportConfig
            from app.services.alert_service import _select_photos, send_alert
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            async with _thread_db() as db:
                result = await db.execute(
                    select(ReportConfig)
                    .where(ReportConfig.source_id == self.source_id, ReportConfig.is_enabled == True)
                    .options(selectinload(ReportConfig.trigger_rules))
                )
                configs = list(result.scalars().all())

                for config in configs:
                    rule_ids = [r.id for r in config.trigger_rules]
                    if event["rule_id"] not in rule_ids:
                        continue

                    photos = []
                    if config.photo_count > 0:
                        from app.services.redis_service import get_redis
                        redis = await get_redis()
                        key = f"photo:{self.source_id}:{event['track_id']}"
                        frames = await redis.lrange(key, 0, -1)
                        photos = _select_photos(frames, config.photo_count)
                        await redis.delete(key)

                    person_name = event.get("person_name") if config.include_person_name else None
                    subject = f"[RanVision] Rule triggered: rule #{event['rule_id']}"
                    body = (
                        f"Source: {self.source_id}\nZone: {event['zone_id']}\n"
                        f"Rule: {event['rule_id']}\n"
                        + (f"Person: {person_name}\n" if person_name else "")
                        + f"Details: {json.dumps(event.get('snapshot', {}))}"
                    )

                    delivered = False
                    delivery_error = None
                    try:
                        await send_alert(config.delivery_method, config.destination, subject, body, photos)
                        delivered = True
                    except Exception as e:
                        delivery_error = str(e)[:500]

                    if config.save_records:
                        record = TriggerRecord(
                            source_id=self.source_id,
                            rule_id=event["rule_id"],
                            zone_id=event["zone_id"],
                            person_name=person_name,
                            rule_snapshot_json=json.dumps(event.get("snapshot", {})),
                            photos_sent=len(photos),
                            alert_delivered=delivered,
                            delivery_error=delivery_error,
                        )
                        db.add(record)
                        await db.commit()

        try:
            asyncio.run(_handle())
        except Exception as e:
            logger.error("Trigger handler error for source %d: %s", self.source_id, e)
