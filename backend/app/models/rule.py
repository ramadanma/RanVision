from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.zone import Zone


class RuleType(str, Enum):
    DWELL_TIME = "dwell_time"
    LIMB_ANGLE = "limb_angle"


class CompareOp(str, Enum):
    GREATER_THAN = "gt"
    LESS_THAN = "lt"


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(16), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # DWELL_TIME fields
    # JSON list of COCO keypoint indices, e.g. "[15, 16]" for both ankles
    keypoint_indices_json: Mapped[str | None] = mapped_column(Text)
    dwell_seconds: Mapped[float | None] = mapped_column(Float)
    dwell_op: Mapped[str | None] = mapped_column(String(4))

    # LIMB_ANGLE fields
    arm_side: Mapped[str | None] = mapped_column(String(8))  # left | right | both
    angle_degrees: Mapped[float | None] = mapped_column(Float)
    angle_op: Mapped[str | None] = mapped_column(String(4))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    zone: Mapped["Zone"] = relationship("Zone", back_populates="rules")
