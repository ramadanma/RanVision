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
    import logging
    logger = logging.getLogger(__name__)

    # Must accept() before any close() call
    await websocket.accept()

    user_id = decode_token(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    async with AsyncSessionLocal() as db:
        try:
            await source_service.get_source(db, source_id, user_id)
        except HTTPException:
            await websocket.close(code=4003, reason="Source not found")
            return

    logger.info("WebSocket client connected for source %d (user %d)", source_id, user_id)
    last_version = 0
    frames_sent = 0
    warned_empty = False
    try:
        while True:
            # Block until a new frame is available — no polling sleep needed.
            # wait_next returns immediately if a newer frame is already in the buffer.
            version, jpeg = await frame_buffer.wait_next(source_id, last_version, timeout=5.0)
            if jpeg:
                await websocket.send_bytes(jpeg)
                last_version = version
                frames_sent += 1
                warned_empty = False
                if frames_sent == 1:
                    logger.info("WS source %d: first frame sent (v=%d, %d bytes)", source_id, version, len(jpeg))
            else:
                if not warned_empty:
                    logger.warning("WS source %d: no frame after 5s (start the stream first)", source_id)
                    warned_empty = True
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from source %d (sent %d frames)", source_id, frames_sent)
    except Exception as e:
        logger.warning("WebSocket error for source %d: %s", source_id, e)


@router.get("/{source_id}/snapshot")
async def get_snapshot(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await source_service.get_source(db, source_id, current_user.id)
    from app.services.frame_buffer import frame_buffer
    _, jpeg = frame_buffer.get(source_id)
    if not jpeg:
        raise HTTPException(status_code=503, detail="No frame available — start the stream first")
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
