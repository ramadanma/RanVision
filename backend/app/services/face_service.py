import logging
import os
import uuid

import numpy as np
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.face import Face

logger = logging.getLogger(__name__)


async def list_faces(db: AsyncSession, user_id: int) -> list[Face]:
    result = await db.execute(select(Face).where(Face.user_id == user_id))
    return list(result.scalars().all())


async def get_face(db: AsyncSession, face_id: int, user_id: int) -> Face:
    face = await db.get(Face, face_id)
    if not face or face.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face not found")
    return face


def _extract_and_save_embedding(photo_path: str, embedding_dir: str) -> str | None:
    """Synchronous: load image, extract embedding, save .npy. Returns path or None."""
    try:
        import cv2
        from app.worker.insightface_stub import extract_embedding
        img = cv2.imread(photo_path)
        if img is None:
            return None
        emb = extract_embedding(img)
        if emb is None:
            logger.warning("No face detected in %s", photo_path)
            return None
        os.makedirs(embedding_dir, exist_ok=True)
        emb_path = os.path.join(embedding_dir, f"{uuid.uuid4().hex}.npy")
        np.save(emb_path, emb)
        return emb_path
    except Exception as e:
        logger.error("Embedding extraction failed for %s: %s", photo_path, e)
        return None


async def create_face(db: AsyncSession, user_id: int, person_name: str, file: UploadFile) -> Face:
    ext = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(settings.uploads_faces, exist_ok=True)
    photo_path = os.path.join(settings.uploads_faces, filename)

    content = await file.read()
    with open(photo_path, "wb") as f:
        f.write(content)

    # Extract embedding in thread pool (blocking CV + model inference)
    import asyncio
    emb_dir = os.path.join(settings.uploads_faces, "embeddings")
    emb_path = await asyncio.get_event_loop().run_in_executor(
        None, _extract_and_save_embedding, photo_path, emb_dir
    )

    face = Face(user_id=user_id, person_name=person_name, photo_path=photo_path, embedding_path=emb_path)
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


def load_embeddings_for_user(user_id: int) -> list[tuple[str, np.ndarray]]:
    """Synchronous: load all face embeddings for a user. Used by worker threads."""
    import asyncio
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

    async def _fetch():
        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with Session() as db:
                result = await db.execute(
                    select(Face).where(Face.user_id == user_id, Face.embedding_path.isnot(None))
                )
                faces = result.scalars().all()
                pairs = []
                for face in faces:
                    try:
                        emb = np.load(face.embedding_path)
                        pairs.append((face.person_name, emb))
                    except Exception:
                        pass
                return pairs
        finally:
            await engine.dispose()

    try:
        return asyncio.run(_fetch())
    except Exception as e:
        logger.error("Failed to load embeddings for user %d: %s", user_id, e)
        return []
