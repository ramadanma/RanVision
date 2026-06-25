from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.rule import Rule


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # JSON array of [x, y] pairs normalized 0-1, e.g. [[0.1,0.2],[0.3,0.4]]
    polygon_json: Mapped[str] = mapped_column(Text, nullable=False)
    npy_path: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    source: Mapped["Source"] = relationship("Source", back_populates="zones")
    rules: Mapped[list["Rule"]] = relationship("Rule", back_populates="zone", cascade="all, delete-orphan")
