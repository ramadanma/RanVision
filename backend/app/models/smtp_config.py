from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SmtpConfig(Base):
    __tablename__ = "smtp_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    host: Mapped[str] = mapped_column(String(256), nullable=False, server_default="")
    port: Mapped[int] = mapped_column(Integer, nullable=False, server_default="587")
    username: Mapped[str] = mapped_column(String(256), nullable=False, server_default="")
    password: Mapped[str] = mapped_column(String(256), nullable=False, server_default="")
    from_addr: Mapped[str] = mapped_column(String(256), nullable=False, server_default="")
    use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
