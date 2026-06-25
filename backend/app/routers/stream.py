import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

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


@router.get("/{source_id}/{segment}")
async def get_segment(
    source_id: int,
    segment: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Only allow .ts segment files
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
