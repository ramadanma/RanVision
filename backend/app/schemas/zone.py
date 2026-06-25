from datetime import datetime

from pydantic import BaseModel


class ZoneCreate(BaseModel):
    source_id: int
    name: str
    polygon: list[list[float]]  # [[x, y], ...] normalized 0-1


class ZoneUpdate(BaseModel):
    name: str | None = None
    polygon: list[list[float]] | None = None


class ZoneOut(BaseModel):
    id: int
    source_id: int
    name: str
    polygon_json: str
    npy_path: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
