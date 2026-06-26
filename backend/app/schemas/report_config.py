from datetime import datetime

from pydantic import BaseModel


class ReportConfigCreate(BaseModel):
    source_id: int
    name: str
    delivery_method: str  # "email" | "webhook"
    destination: str
    photo_count: int = 0
    include_person_name: bool = False
    save_records: bool = True
    subject_template: str | None = None
    body_template: str | None = None


class ReportConfigUpdate(BaseModel):
    name: str | None = None
    delivery_method: str | None = None
    destination: str | None = None
    photo_count: int | None = None
    include_person_name: bool | None = None
    save_records: bool | None = None
    is_enabled: bool | None = None
    subject_template: str | None = None
    body_template: str | None = None


class ReportConfigOut(BaseModel):
    id: int
    source_id: int
    name: str
    delivery_method: str
    destination: str
    photo_count: int
    include_person_name: bool
    save_records: bool
    is_enabled: bool
    subject_template: str | None
    body_template: str | None
    trigger_rule_ids: list[int] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
