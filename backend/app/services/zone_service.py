import json
import os

import numpy as np
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.zone import Zone


async def list_zones(db: AsyncSession, source_id: int) -> list[Zone]:
    result = await db.execute(select(Zone).where(Zone.source_id == source_id))
    return list(result.scalars().all())


async def get_zone(db: AsyncSession, zone_id: int) -> Zone:
    zone = await db.get(Zone, zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone


def _save_npy(zone_id: int, polygon: list[list[float]]) -> str:
    os.makedirs(settings.uploads_zones, exist_ok=True)
    path = os.path.join(settings.uploads_zones, f"{zone_id}.npy")
    np.save(path, np.array(polygon, dtype=np.float32))
    return path


async def create_zone(db: AsyncSession, source_id: int, name: str, polygon: list[list[float]]) -> Zone:
    zone = Zone(source_id=source_id, name=name, polygon_json=json.dumps(polygon))
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    zone.npy_path = _save_npy(zone.id, polygon)
    await db.commit()
    await db.refresh(zone)
    return zone


async def update_zone(db: AsyncSession, zone: Zone, name: str | None, polygon: list[list[float]] | None) -> Zone:
    if name is not None:
        zone.name = name
    if polygon is not None:
        zone.polygon_json = json.dumps(polygon)
        zone.npy_path = _save_npy(zone.id, polygon)
    await db.commit()
    await db.refresh(zone)
    return zone


async def delete_zone(db: AsyncSession, zone: Zone) -> None:
    if zone.npy_path and os.path.exists(zone.npy_path):
        os.remove(zone.npy_path)
    await db.delete(zone)
    await db.commit()
