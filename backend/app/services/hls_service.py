import os
import subprocess
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from app.models.source import Source


class HLSManager:
    """Manages ffmpeg subprocesses that transcode video sources to HLS."""

    def __init__(self):
        self._processes: dict[int, subprocess.Popen] = {}

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

    def start(self, source: "Source") -> None:
        source_id = source.id
        if source_id in self._processes:
            proc = self._processes[source_id]
            if proc.poll() is None:
                return  # already running

        output_dir = self._get_output_dir(source_id)
        source.hls_output_dir = output_dir
        cmd = self._build_ffmpeg_cmd(source, output_dir)

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._processes[source_id] = proc

    def stop(self, source_id: int) -> None:
        proc = self._processes.pop(source_id, None)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def is_running(self, source_id: int) -> bool:
        proc = self._processes.get(source_id)
        return proc is not None and proc.poll() is None

    def stop_all(self) -> None:
        for source_id in list(self._processes.keys()):
            self.stop(source_id)


hls_manager = HLSManager()
