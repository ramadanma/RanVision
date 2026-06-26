from datetime import datetime

from pydantic import BaseModel


class SourceCreate(BaseModel):
    name: str
    source_type: str  # "file" | "ip_camera"
    file_path: str | None = None
    ip: str | None = None
    port: int | None = 554
    cam_username: str | None = None
    cam_password: str | None = None
    transport: str | None = "tcp"


class SourceUpdate(BaseModel):
    name: str | None = None
    ip: str | None = None
    port: int | None = None
    cam_username: str | None = None
    cam_password: str | None = None
    transport: str | None = None


class SourceOut(BaseModel):
    id: int
    name: str
    source_type: str
    file_path: str | None
    ip: str | None
    port: int | None
    cam_username: str | None
    transport: str | None
    rtsp_url: str | None
    is_active: bool
    show_overlay: bool
    face_recognition_enabled: bool
    face_check_front: bool
    show_skeleton: bool
    detection_roi_json: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
