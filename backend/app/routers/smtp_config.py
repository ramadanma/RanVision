from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.smtp_config import SmtpConfigOut, SmtpConfigUpdate
from app.services import smtp_config_service

router = APIRouter(prefix="/smtp-config", tags=["smtp-config"])


@router.get("", response_model=SmtpConfigOut)
async def get_smtp_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await smtp_config_service.get_smtp_config(db)
    return SmtpConfigOut(
        host=config.host,
        port=config.port,
        username=config.username,
        from_addr=config.from_addr,
        use_tls=config.use_tls,
    )


@router.patch("", response_model=SmtpConfigOut)
async def update_smtp_config(
    body: SmtpConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await smtp_config_service.update_smtp_config(db, body.model_dump(exclude_none=True))
    return SmtpConfigOut(
        host=config.host,
        port=config.port,
        username=config.username,
        from_addr=config.from_addr,
        use_tls=config.use_tls,
    )
