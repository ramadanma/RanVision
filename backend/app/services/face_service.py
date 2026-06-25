import os
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.face import Face


async def list_faces(db: AsyncSession, user_id: int) -> list[Face]:
    result = await db.execute(select(Face).where(Face.user_id == user_id))
    return list(result.scalars().all())


async def get_face(db: AsyncSession, face_id: int, user_id: int) -> Face:
    face = await db.get(Face, face_id)
    if not face or face.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face not found")
    return face


async def create_face(db: AsyncSession, user_id: int, person_name: str, file: UploadFile) -> Face:
    ext = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(settings.uploads_faces, exist_ok=True)
    path = os.path.join(settings.uploads_faces, filename)

    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    face = Face(user_id=user_id, person_name=person_name, photo_path=path)
    db.add(face)
    await db.commit()
    await db.refresh(face)
    return face


async def update_face(db: AsyncSession, face: Face, person_name: str) -> Face:
    face.person_name = person_name
    await db.commit()
    await db.refresh(face)
    return face


async def delete_face(db: AsyncSession, face: Face) -> None:
    if face.photo_path and os.path.exists(face.photo_path):
        os.remove(face.photo_path)
    if face.embedding_path and os.path.exists(face.embedding_path):
        os.remove(face.embedding_path)
    await db.delete(face)
    await db.commit()
