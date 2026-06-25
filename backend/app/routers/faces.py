from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.face import FaceOut, FaceUpdate
from app.services import face_service

router = APIRouter(prefix="/faces", tags=["faces"])


@router.get("", response_model=list[FaceOut])
async def list_faces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await face_service.list_faces(db, current_user.id)


@router.post("", response_model=FaceOut, status_code=status.HTTP_201_CREATED)
async def upload_face(
    person_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await face_service.create_face(db, current_user.id, person_name, file)


@router.patch("/{face_id}", response_model=FaceOut)
async def update_face(
    face_id: int,
    body: FaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    face = await face_service.get_face(db, face_id, current_user.id)
    return await face_service.update_face(db, face, body.person_name)


@router.delete("/{face_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_face(
    face_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    face = await face_service.get_face(db, face_id, current_user.id)
    await face_service.delete_face(db, face)
