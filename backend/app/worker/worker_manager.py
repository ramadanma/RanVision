import logging

from app.worker.stream_processor import StreamProcessor

logger = logging.getLogger(__name__)


class WorkerManager:
    def __init__(self):
        self._workers: dict[int, StreamProcessor] = {}

    def start(self, source_id: int, user_id: int = 0) -> None:
        existing = self._workers.get(source_id)
        if existing and existing.is_alive():
            return
        worker = StreamProcessor(source_id, user_id)
        worker.start()
        self._workers[source_id] = worker
        logger.info("Started worker for source %d (user %d)", source_id, user_id)

    def stop(self, source_id: int) -> None:
        worker = self._workers.pop(source_id, None)
        if worker:
            worker.stop()
            worker.join(timeout=5)
            logger.info("Stopped worker for source %d", source_id)

    def stop_all(self) -> None:
        for source_id in list(self._workers.keys()):
            self.stop(source_id)


worker_manager = WorkerManager()
