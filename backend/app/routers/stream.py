import asyncio
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import source_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/stream", tags=["stream"])


def _segment_path(source_id: int, filename: str) -> str:
    return os.path.join(settings.HLS_SEGMENTS_DIR, str(source_id), filename)


@router.get("/{source_id}/index.m3u8")
async def get_manifest(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await source_service.get_source(db, source_id, current_user.id)
    path = _segment_path(source_id, "index.m3u8")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Stream not started or not ready")
    return FileResponse(path, media_type="application/vnd.apple.mpegurl")


@router.websocket("/{source_id}/ws")
async def stream_ws(
    source_id: int,
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket live stream: pushes JPEG frames as binary messages."""
    from app.dependencies import decode_token
    from app.database import AsyncSessionLocal
    from app.services.frame_buffer import frame_buffer

    # Authenticate via query-param token
    user_id = decode_token(token)
    if user_id is None:
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        try:
            source = await source_service.get_source(db, source_id, user_id)
        except HTTPException:
            await websocket.close(code=4003)
            return

    if not source.is_active:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    last_version = 0
    try:
        while True:
            version, jpeg = frame_buffer.get(source_id)
            if version > last_version and jpeg:
                await websocket.send_bytes(jpeg)
                last_version = version
            else:
                await asyncio.sleep(0.05)  # poll at 20fps max
    except WebSocketDisconnect:
        pass


@router.get("/{source_id}/snapshot")
async def get_snapshot(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await source_service.get_source(db, source_id, current_user.id)
    manifest = _segment_path(source_id, "index.m3u8")
    if not os.path.exists(manifest):
        raise HTTPException(status_code=404, detail="Stream not started")

    def _grab():
        import glob, subprocess, tempfile
        segment_dir = os.path.dirname(manifest)
        ts_files = sorted(glob.glob(os.path.join(segment_dir, "*.ts")))
        if not ts_files:
            return None
        latest_ts = ts_files[-1]
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", latest_ts, "-frames:v", "1", "-q:v", "2", tmp_path],
                capture_output=True, timeout=5,
            )
            if r.returncode != 0 or not os.path.exists(tmp_path):
                return None
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    jpeg = await asyncio.get_event_loop().run_in_executor(None, _grab)
    if jpeg is None:
        raise HTTPException(status_code=503, detail="No frame available yet")
    return Response(content=jpeg, media_type="image/jpeg")


@router.get("/{source_id}/{segment}")
async def get_segment(
    source_id: int,
    segment: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not segment.endswith(".ts"):
        raise HTTPException(status_code=400, detail="Invalid segment")
    await source_service.get_source(db, source_id, current_user.id)
    path = _segment_path(source_id, segment)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Segment not found")
    return FileResponse(path, media_type="video/mp2t")


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(settings.uploads_videos, exist_ok=True)
    path = os.path.join(settings.uploads_videos, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"file_path": path, "filename": filename}
