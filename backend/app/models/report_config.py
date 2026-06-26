from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.rule import Rule


class DeliveryMethod(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"


class ReportConfigRule(Base):
    """Junction table: which rules trigger a report config."""
    __tablename__ = "report_config_rules"

    report_config_id: Mapped[int] = mapped_column(
        ForeignKey("report_configs.id", ondelete="CASCADE"), primary_key=True
    )
    rule_id: Mapped[int] = mapped_column(
        ForeignKey("rules.id", ondelete="CASCADE"), primary_key=True
    )


class ReportConfig(Base):
    __tablename__ = "report_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    delivery_method: Mapped[str] = mapped_column(String(16), nullable=False)
    destination: Mapped[str] = mapped_column(String(256), nullable=False)
    photo_count: Mapped[int] = mapped_column(Integer, default=0)
    include_person_name: Mapped[bool] = mapped_column(Boolean, default=False)
    save_records: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    subject_template: Mapped[str | None] = mapped_column(Text)
    body_template: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    source: Mapped["Source"] = relationship("Source", back_populates="report_configs")
    trigger_rules: Mapped[list["Rule"]] = relationship("Rule", secondary="report_config_rules")
