import logging
import os
import subprocess
import threading
import time
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from app.models.source import Source

logger = logging.getLogger(__name__)


class HLSManager:
    """Manages ffmpeg subprocesses that transcode video sources to HLS."""

    def __init__(self):
        self._processes: dict[int, subprocess.Popen] = {}
        self._sources: dict[int, "Source"] = {}  # keep source for restart
        self._log_files: dict[int, object] = {}
        self._stopped: set[int] = set()  # explicitly stopped, don't restart
        self._watchdog: threading.Thread | None = None
        self._watchdog_running = False

    def _get_output_dir(self, source_id: int) -> str:
        path = os.path.join(settings.HLS_SEGMENTS_DIR, str(source_id))
        os.makedirs(path, exist_ok=True)
        return path

    def _build_ffmpeg_cmd(self, source: "Source", output_dir: str) -> list[str]:
        manifest = os.path.join(output_dir, "index.m3u8")
        hls_args = [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-an",
            "-f", "hls",
            "-hls_time", "2",
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments",
            manifest,
        ]

        if source.source_type == "file":
            return [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-re",
                "-i", source.file_path,
                *hls_args,
            ]
        else:
            transport = source.transport or "tcp"
            from app.services.source_service import build_rtsp_url
            rtsp = build_rtsp_url(source)
            return [
                "ffmpeg", "-y",
                "-rtsp_transport", transport,
                "-i", rtsp,
                *hls_args,
            ]

    def _spawn(self, source: "Source") -> None:
        source_id = source.id
        output_dir = self._get_output_dir(source_id)
        cmd = self._build_ffmpeg_cmd(source, output_dir)
        log_path = os.path.join(output_dir, "ffmpeg.log")
        # Append mode so we don't lose previous crash info
        log_file = open(log_path, "a")
        if source_id in self._log_files:
            try:
                self._log_files[source_id].close()
            except Exception:
                pass
        self._log_files[source_id] = log_file
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=log_file)
        self._processes[source_id] = proc
        logger.info("ffmpeg started for source %d (pid=%d)", source_id, proc.pid)

    def start(self, source: "Source") -> None:
        source_id = source.id
        self._stopped.discard(source_id)
        self._sources[source_id] = source
        if source_id in self._processes and self._processes[source_id].poll() is None:
            return  # already running
        self._spawn(source)
        self._ensure_watchdog()

    def stop(self, source_id: int) -> None:
        self._stopped.add(source_id)
        self._sources.pop(source_id, None)
        proc = self._processes.pop(source_id, None)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        lf = self._log_files.pop(source_id, None)
        if lf:
            try:
                lf.close()
            except Exception:
                pass

    def is_running(self, source_id: int) -> bool:
        proc = self._processes.get(source_id)
        return proc is not None and proc.poll() is None

    def stop_all(self) -> None:
        self._watchdog_running = False
        for source_id in list(self._processes.keys()):
            self.stop(source_id)

    def _ensure_watchdog(self) -> None:
        if self._watchdog and self._watchdog.is_alive():
            return
        self._watchdog_running = True
        self._watchdog = threading.Thread(target=self._watch_loop, daemon=True, name="hls-watchdog")
        self._watchdog.start()

    def _watch_loop(self) -> None:
        while self._watchdog_running:
            time.sleep(5)
            for source_id, proc in list(self._processes.items()):
                if source_id in self._stopped:
                    continue
                if proc.poll() is not None:
                    logger.warning("ffmpeg for source %d exited (rc=%d), restarting", source_id, proc.returncode)
                    source = self._sources.get(source_id)
                    if source:
                        try:
                            self._spawn(source)
                        except Exception as e:
                            logger.error("Failed to restart ffmpeg for source %d: %s", source_id, e)


hls_manager = HLSManager()
