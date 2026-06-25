from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.rule import RuleCreate, RuleOut, RuleUpdate
from app.services import rule_service, source_service, zone_service

router = APIRouter(prefix="/rules", tags=["rules"])


async def _verify_zone_ownership(zone_id: int, user: User, db: AsyncSession):
    zone = await zone_service.get_zone(db, zone_id)
    await source_service.get_source(db, zone.source_id, user.id)
    return zone


@router.get("", response_model=list[RuleOut])
async def list_rules(
    zone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_zone_ownership(zone_id, current_user, db)
    return await rule_service.list_rules(db, zone_id)


@router.post("", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: RuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_zone_ownership(body.zone_id, current_user, db)
    return await rule_service.create_rule(db, body.model_dump())


@router.get("/{rule_id}", response_model=RuleOut)
async def get_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = await rule_service.get_rule(db, rule_id)
    await _verify_zone_ownership(rule.zone_id, current_user, db)
    return rule


@router.patch("/{rule_id}", response_model=RuleOut)
async def update_rule(
    rule_id: int,
    body: RuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = await rule_service.get_rule(db, rule_id)
    await _verify_zone_ownership(rule.zone_id, current_user, db)
    return await rule_service.update_rule(db, rule, body.model_dump(exclude_none=True))


@router.patch("/{rule_id}/toggle", response_model=RuleOut)
async def toggle_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = await rule_service.get_rule(db, rule_id)
    await _verify_zone_ownership(rule.zone_id, current_user, db)
    return await rule_service.toggle_rule(db, rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = await rule_service.get_rule(db, rule_id)
    await _verify_zone_ownership(rule.zone_id, current_user, db)
    await rule_service.delete_rule(db, rule)
