import json

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule


async def list_rules(db: AsyncSession, zone_id: int) -> list[Rule]:
    result = await db.execute(select(Rule).where(Rule.zone_id == zone_id))
    return list(result.scalars().all())


async def get_rule(db: AsyncSession, rule_id: int) -> Rule:
    rule = await db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule


async def create_rule(db: AsyncSession, data: dict) -> Rule:
    keypoint_indices = data.pop("keypoint_indices", None)
    rule = Rule(**data)
    if keypoint_indices is not None:
        rule.keypoint_indices_json = json.dumps(keypoint_indices)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def update_rule(db: AsyncSession, rule: Rule, data: dict) -> Rule:
    keypoint_indices = data.pop("keypoint_indices", None)
    for k, v in data.items():
        if v is not None:
            setattr(rule, k, v)
    if keypoint_indices is not None:
        rule.keypoint_indices_json = json.dumps(keypoint_indices)
    await db.commit()
    await db.refresh(rule)
    return rule


async def toggle_rule(db: AsyncSession, rule: Rule) -> Rule:
    rule.is_enabled = not rule.is_enabled
    await db.commit()
    await db.refresh(rule)
    return rule


async def delete_rule(db: AsyncSession, rule: Rule) -> None:
    await db.delete(rule)
    await db.commit()
