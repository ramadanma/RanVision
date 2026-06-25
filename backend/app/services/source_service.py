import os

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.services.encryption import decrypt, encrypt


def build_rtsp_url(source: Source) -> str:
    cam_pass = ""
    if source.cam_password_enc:
        try:
            cam_pass = decrypt(source.cam_password_enc)
        except Exception:
            cam_pass = ""
    creds = f"{source.cam_username}:{cam_pass}@" if source.cam_username else ""
    return f"rtsp://{creds}{source.ip}:{source.port or 554}/stream"


async def list_sources(db: AsyncSession, user_id: int) -> list[Source]:
    result = await db.execute(select(Source).where(Source.user_id == user_id))
    return list(result.scalars().all())


async def get_source(db: AsyncSession, source_id: int, user_id: int) -> Source:
    source = await db.get(Source, source_id)
    if not source or source.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


async def create_source(db: AsyncSession, user_id: int, data: dict) -> Source:
    cam_password = data.pop("cam_password", None)
    source = Source(user_id=user_id, **data)
    if cam_password:
        source.cam_password_enc = encrypt(cam_password)
    if source.source_type == "ip_camera":
        source.rtsp_url = build_rtsp_url(source)
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def update_source(db: AsyncSession, source: Source, data: dict) -> Source:
    cam_password = data.pop("cam_password", None)
    for k, v in data.items():
        if v is not None:
            setattr(source, k, v)
    if cam_password is not None:
        source.cam_password_enc = encrypt(cam_password)
    if source.source_type == "ip_camera":
        source.rtsp_url = build_rtsp_url(source)
    await db.commit()
    await db.refresh(source)
    return source


async def delete_source(db: AsyncSession, source: Source) -> None:
    await db.delete(source)
    await db.commit()
