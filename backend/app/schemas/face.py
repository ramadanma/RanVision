from datetime import datetime

from pydantic import BaseModel


class FaceUpdate(BaseModel):
    person_name: str


class FaceOut(BaseModel):
    id: int
    user_id: int
    person_name: str
    photo_path: str
    embedding_path: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
