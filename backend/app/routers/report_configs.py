from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report_config import ReportConfigCreate, ReportConfigOut, ReportConfigUpdate
from app.services import report_config_service, source_service

router = APIRouter(prefix="/report-configs", tags=["report-configs"])


async def _verify_source_ownership(source_id: int, user: User, db: AsyncSession):
    await source_service.get_source(db, source_id, user.id)


def _to_out(config) -> ReportConfigOut:
    out = ReportConfigOut.model_validate(config)
    out.trigger_rule_ids = [r.id for r in config.trigger_rules]
    return out


@router.get("", response_model=list[ReportConfigOut])
async def list_report_configs(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_source_ownership(source_id, current_user, db)
    configs = await report_config_service.list_report_configs(db, source_id)
    return [_to_out(c) for c in configs]


@router.post("", response_model=ReportConfigOut, status_code=status.HTTP_201_CREATED)
async def create_report_config(
    body: ReportConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_source_ownership(body.source_id, current_user, db)
    config = await report_config_service.create_report_config(db, body.model_dump())
    return _to_out(config)


@router.get("/{config_id}", response_model=ReportConfigOut)
async def get_report_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await report_config_service.get_report_config(db, config_id)
    await _verify_source_ownership(config.source_id, current_user, db)
    return _to_out(config)


@router.patch("/{config_id}", response_model=ReportConfigOut)
async def update_report_config(
    config_id: int,
    body: ReportConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await report_config_service.get_report_config(db, config_id)
    await _verify_source_ownership(config.source_id, current_user, db)
    config = await report_config_service.update_report_config(db, config, body.model_dump(exclude_none=True))
    return _to_out(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await report_config_service.get_report_config(db, config_id)
    await _verify_source_ownership(config.source_id, current_user, db)
    await report_config_service.delete_report_config(db, config)


@router.post("/{config_id}/trigger-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_trigger_rule(
    config_id: int,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await report_config_service.get_report_config(db, config_id)
    await _verify_source_ownership(config.source_id, current_user, db)
    await report_config_service.add_trigger_rule(db, config_id, rule_id)


@router.delete("/{config_id}/trigger-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_trigger_rule(
    config_id: int,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await report_config_service.get_report_config(db, config_id)
    await _verify_source_ownership(config.source_id, current_user, db)
    await report_config_service.remove_trigger_rule(db, config_id, rule_id)
