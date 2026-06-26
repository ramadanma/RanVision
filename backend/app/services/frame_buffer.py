"""In-memory latest-frame buffer shared between StreamProcessor and WebSocket clients."""
import asyncio
import threading


class FrameBuffer:
    def __init__(self):
        self._frames: dict[int, bytes] = {}
        self._version: dict[int, int] = {}
        self._lock = threading.Lock()
        # asyncio.Event per source — set by worker thread via call_soon_threadsafe,
        # awaited by WebSocket coroutines. Protected by _ev_lock for dict mutations only.
        self._events: dict[int, asyncio.Event] = {}
        self._ev_lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def push(self, source_id: int, jpeg: bytes) -> None:
        with self._lock:
            self._frames[source_id] = jpeg
            self._version[source_id] = self._version.get(source_id, 0) + 1
        # Wake up all async waiters from the sync worker thread
        with self._ev_lock:
            loop = self._loop
            evt = self._events.get(source_id)
        if loop and evt:
            loop.call_soon_threadsafe(evt.set)

    def get(self, source_id: int) -> tuple[int, bytes | None]:
        with self._lock:
            return self._version.get(source_id, 0), self._frames.get(source_id)

    async def wait_next(
        self, source_id: int, last_version: int, timeout: float = 5.0
    ) -> tuple[int, bytes | None]:
        """Block until a frame newer than last_version arrives (or timeout).

        Must be called from an async context (WebSocket handler).
        Multiple coroutines can wait on the same source simultaneously.
        """
        with self._ev_lock:
            if self._loop is None:
                self._loop = asyncio.get_running_loop()
            if source_id not in self._events:
                self._events[source_id] = asyncio.Event()
            evt = self._events[source_id]

        while True:
            version, jpeg = self.get(source_id)
            if version > last_version and jpeg:
                return version, jpeg
            # Clear before re-checking to avoid missing a push that arrived
            # between the check above and the clear here.
            evt.clear()
            version, jpeg = self.get(source_id)
            if version > last_version and jpeg:
                return version, jpeg
            try:
                await asyncio.wait_for(evt.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                # Return current state (jpeg may still be None if stream not started)
                return self.get(source_id)

    def clear(self, source_id: int) -> None:
        with self._lock:
            self._frames.pop(source_id, None)
            self._version.pop(source_id, None)
        with self._ev_lock:
            self._events.pop(source_id, None)


frame_buffer = FrameBuffer()
