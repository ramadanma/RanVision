from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.zone import ZoneCreate, ZoneOut, ZoneUpdate
from app.services import source_service, zone_service

router = APIRouter(prefix="/zones", tags=["zones"])


async def _verify_source_ownership(source_id: int, user: User, db: AsyncSession):
    await source_service.get_source(db, source_id, user.id)


@router.get("", response_model=list[ZoneOut])
async def list_zones(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_source_ownership(source_id, current_user, db)
    return await zone_service.list_zones(db, source_id)


@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
async def create_zone(
    body: ZoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_source_ownership(body.source_id, current_user, db)
    if len(body.polygon) < 4:
        raise HTTPException(status_code=400, detail="Polygon must have at least 4 points")
    return await zone_service.create_zone(db, body.source_id, body.name, body.polygon)


@router.get("/{zone_id}", response_model=ZoneOut)
async def get_zone(
    zone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    zone = await zone_service.get_zone(db, zone_id)
    await _verify_source_ownership(zone.source_id, current_user, db)
    return zone


@router.patch("/{zone_id}", response_model=ZoneOut)
async def update_zone(
    zone_id: int,
    body: ZoneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    zone = await zone_service.get_zone(db, zone_id)
    await _verify_source_ownership(zone.source_id, current_user, db)
    if body.polygon and len(body.polygon) < 4:
        raise HTTPException(status_code=400, detail="Polygon must have at least 4 points")
    return await zone_service.update_zone(db, zone, body.name, body.polygon)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    zone = await zone_service.get_zone(db, zone_id)
    await _verify_source_ownership(zone.source_id, current_user, db)
    await zone_service.delete_zone(db, zone)
