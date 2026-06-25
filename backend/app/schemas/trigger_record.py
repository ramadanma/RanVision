from datetime import datetime

from pydantic import BaseModel


class TriggerRecordOut(BaseModel):
    id: int
    source_id: int
    rule_id: int | None
    zone_id: int | None
    person_name: str | None
    triggered_at: datetime
    rule_snapshot_json: str | None
    photos_sent: int
    alert_delivered: bool
    delivery_error: str | None

    model_config = {"from_attributes": True}


class PaginatedRecords(BaseModel):
    total: int
    page: int
    size: int
    items: list[TriggerRecordOut]
