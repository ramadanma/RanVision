from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.zone import Zone
    from app.models.report_config import ReportConfig
    from app.models.trigger_record import TriggerRecord


class SourceType(str, Enum):
    FILE = "file"
    IP_CAMERA = "ip_camera"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)

    # FILE type
    file_path: Mapped[str | None] = mapped_column(String(512))

    # IP_CAMERA type
    ip: Mapped[str | None] = mapped_column(String(64))
    port: Mapped[int | None] = mapped_column(Integer, default=554)
    cam_username: Mapped[str | None] = mapped_column(String(64))
    cam_password_enc: Mapped[str | None] = mapped_column(String(512))
    transport: Mapped[str | None] = mapped_column(String(8))
    rtsp_url: Mapped[str | None] = mapped_column(String(512))

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    show_overlay: Mapped[bool] = mapped_column(Boolean, default=True)
    face_recognition_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    face_check_front: Mapped[bool] = mapped_column(Boolean, default=False)
    show_skeleton: Mapped[bool] = mapped_column(Boolean, default=False)
    detection_roi_json: Mapped[str | None] = mapped_column(Text)
    hls_output_dir: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="sources")
    zones: Mapped[list["Zone"]] = relationship("Zone", back_populates="source", cascade="all, delete-orphan")
    report_configs: Mapped[list["ReportConfig"]] = relationship("ReportConfig", back_populates="source", cascade="all, delete-orphan")
    trigger_records: Mapped[list["TriggerRecord"]] = relationship("TriggerRecord", back_populates="source", cascade="all, delete-orphan")
