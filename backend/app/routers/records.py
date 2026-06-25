from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.trigger_record import TriggerRecord
from app.models.user import User
from app.schemas.trigger_record import PaginatedRecords, TriggerRecordOut
from app.services import source_service

router = APIRouter(prefix="/records", tags=["records"])


@router.get("", response_model=PaginatedRecords)
async def list_records(
    source_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await source_service.get_source(db, source_id, current_user.id)
    offset = (page - 1) * size

    total_result = await db.execute(
        select(func.count()).where(TriggerRecord.source_id == source_id)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(TriggerRecord)
        .where(TriggerRecord.source_id == source_id)
        .order_by(TriggerRecord.triggered_at.desc())
        .offset(offset)
        .limit(size)
    )
    items = list(result.scalars().all())
    return PaginatedRecords(total=total, page=page, size=size, items=items)


@router.get("/{record_id}", response_model=TriggerRecordOut)
async def get_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(TriggerRecord, record_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Record not found")
    await source_service.get_source(db, record.source_id, current_user.id)
    return record


@router.post("/test-trigger", status_code=status.HTTP_200_OK)
async def test_trigger(
    source_id: int,
    rule_id: int,
    zone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually fire a fake trigger event to test the alert pipeline."""
    await source_service.get_source(db, source_id, current_user.id)
    from app.worker.stream_processor import StreamProcessor
    processor = StreamProcessor(source_id)
    processor._on_trigger({
        "rule_id": rule_id,
        "zone_id": zone_id,
        "track_id": 0,
        "person_name": "test",
        "snapshot": {"note": "manual test trigger"},
    })
    return {"status": "trigger fired", "source_id": source_id, "rule_id": rule_id}


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(TriggerRecord, record_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Record not found")
    await source_service.get_source(db, record.source_id, current_user.id)
    await db.delete(record)
    await db.commit()
