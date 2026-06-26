from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.source import SourceCreate, SourceOut, SourceUpdate
from app.services import source_service


class DetectionRoiUpdate(BaseModel):
    roi_json: str | None = None

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def list_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await source_service.list_sources(db, current_user.id)


@router.post("", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: SourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump()
    return await source_service.create_source(db, current_user.id, data)


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await source_service.get_source(db, source_id, current_user.id)


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(
    source_id: int,
    body: SourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = await source_service.get_source(db, source_id, current_user.id)
    return await source_service.update_source(db, source, body.model_dump(exclude_none=True))


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.hls_service import hls_manager
    from app.worker.worker_manager import worker_manager
    source = await source_service.get_source(db, source_id, current_user.id)
    hls_manager.stop(source_id)
    worker_manager.stop(source_id)
    await source_service.delete_source(db, source)


@router.post("/{source_id}/start", response_model=SourceOut)
async def start_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.hls_service import hls_manager
    from app.worker.worker_manager import worker_manager
    source = await source_service.get_source(db, source_id, current_user.id)
    hls_manager.start(source)
    worker_manager.start(source_id, source.user_id)
    source.is_active = True
    await db.commit()
    await db.refresh(source)
    return source


@router.post("/{source_id}/stop", response_model=SourceOut)
async def stop_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.hls_service import hls_manager
    from app.worker.worker_manager import worker_manager
    source = await source_service.get_source(db, source_id, current_user.id)
    hls_manager.stop(source_id)
    worker_manager.stop(source_id)
    source.is_active = False
    await db.commit()
    await db.refresh(source)
    return source


@router.patch("/{source_id}/overlay", response_model=SourceOut)
async def toggle_overlay(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = await source_service.get_source(db, source_id, current_user.id)
    source.show_overlay = not source.show_overlay
    await db.commit()
    await db.refresh(source)
    return source


@router.patch("/{source_id}/face-recognition", response_model=SourceOut)
async def toggle_face_recognition(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = await source_service.get_source(db, source_id, current_user.id)
    source.face_recognition_enabled = not source.face_recognition_enabled
    await db.commit()
    await db.refresh(source)
    return source


@router.patch("/{source_id}/face-check-front", response_model=SourceOut)
async def toggle_face_check_front(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = await source_service.get_source(db, source_id, current_user.id)
    source.face_check_front = not source.face_check_front
    await db.commit()
    await db.refresh(source)
    return source


@router.patch("/{source_id}/show-skeleton", response_model=SourceOut)
async def toggle_show_skeleton(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = await source_service.get_source(db, source_id, current_user.id)
    source.show_skeleton = not source.show_skeleton
    await db.commit()
    await db.refresh(source)
    return source


@router.patch("/{source_id}/detection-roi", response_model=SourceOut)
async def update_detection_roi(
    source_id: int,
    body: DetectionRoiUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = await source_service.get_source(db, source_id, current_user.id)
    source.detection_roi_json = body.roi_json
    await db.commit()
    await db.refresh(source)
    return source
