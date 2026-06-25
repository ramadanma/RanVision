from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report_config import ReportConfig, ReportConfigRule
from app.models.rule import Rule


async def list_report_configs(db: AsyncSession, source_id: int) -> list[ReportConfig]:
    result = await db.execute(
        select(ReportConfig)
        .where(ReportConfig.source_id == source_id)
        .options(selectinload(ReportConfig.trigger_rules))
    )
    return list(result.scalars().all())


async def get_report_config(db: AsyncSession, config_id: int) -> ReportConfig:
    result = await db.execute(
        select(ReportConfig)
        .where(ReportConfig.id == config_id)
        .options(selectinload(ReportConfig.trigger_rules))
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report config not found")
    return config


async def create_report_config(db: AsyncSession, data: dict) -> ReportConfig:
    config = ReportConfig(**data)
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def update_report_config(db: AsyncSession, config: ReportConfig, data: dict) -> ReportConfig:
    for k, v in data.items():
        if v is not None:
            setattr(config, k, v)
    await db.commit()
    await db.refresh(config)
    return config


async def delete_report_config(db: AsyncSession, config: ReportConfig) -> None:
    await db.delete(config)
    await db.commit()


async def add_trigger_rule(db: AsyncSession, config_id: int, rule_id: int) -> None:
    existing = await db.get(ReportConfigRule, (config_id, rule_id))
    if existing:
        return
    junction = ReportConfigRule(report_config_id=config_id, rule_id=rule_id)
    db.add(junction)
    await db.commit()


async def remove_trigger_rule(db: AsyncSession, config_id: int, rule_id: int) -> None:
    junction = await db.get(ReportConfigRule, (config_id, rule_id))
    if junction:
        await db.delete(junction)
        await db.commit()
