"""In-memory latest-frame buffer shared between StreamProcessor and WebSocket clients."""
import threading


class FrameBuffer:
    def __init__(self):
        self._frames: dict[int, bytes] = {}   # source_id -> latest JPEG bytes
        self._version: dict[int, int] = {}    # source_id -> monotonic counter
        self._lock = threading.Lock()

    def push(self, source_id: int, jpeg: bytes) -> None:
        with self._lock:
            self._frames[source_id] = jpeg
            self._version[source_id] = self._version.get(source_id, 0) + 1

    def get(self, source_id: int) -> tuple[int, bytes | None]:
        """Returns (version, jpeg). version=0 means no frame yet."""
        with self._lock:
            return self._version.get(source_id, 0), self._frames.get(source_id)

    def clear(self, source_id: int) -> None:
        with self._lock:
            self._frames.pop(source_id, None)
            self._version.pop(source_id, None)


frame_buffer = FrameBuffer()
