from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.rule import Rule
    from app.models.zone import Zone


class TriggerRecord(Base):
    __tablename__ = "trigger_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id", ondelete="SET NULL"), nullable=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    person_name: Mapped[str | None] = mapped_column(String(128))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    rule_snapshot_json: Mapped[str | None] = mapped_column(Text)
    photos_sent: Mapped[int] = mapped_column(Integer, default=0)
    alert_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_error: Mapped[str | None] = mapped_column(String(512))

    source: Mapped["Source"] = relationship("Source", back_populates="trigger_records")
