import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
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


@router.get("/{face_id}/photo")
async def get_face_photo(
    face_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    face = await face_service.get_face(db, face_id, current_user.id)
    if not os.path.exists(face.photo_path):
        raise HTTPException(status_code=404, detail="Photo file not found")
    return FileResponse(face.photo_path)


@router.post("/{face_id}/reextract", response_model=FaceOut)
async def reextract_embedding(
    face_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run face embedding extraction for a face whose embedding_path is None."""
    import asyncio
    from app.config import settings
    face = await face_service.get_face(db, face_id, current_user.id)
    emb_dir = os.path.join(settings.uploads_faces, "embeddings")
    emb_path = await asyncio.get_event_loop().run_in_executor(
        None, face_service._extract_and_save_embedding, face.photo_path, emb_dir
    )
    face.embedding_path = emb_path
    await db.commit()
    await db.refresh(face)
    if emb_path is None:
        raise HTTPException(status_code=422, detail="未能从该照片中检测到人脸，请换一张清晰的正脸照")
    return face


@router.delete("/{face_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_face(
    face_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    face = await face_service.get_face(db, face_id, current_user.id)
    await face_service.delete_face(db, face)
