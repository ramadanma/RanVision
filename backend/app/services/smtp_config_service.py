from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smtp_config import SmtpConfig


async def get_smtp_config(db: AsyncSession) -> SmtpConfig:
    result = await db.execute(select(SmtpConfig).where(SmtpConfig.id == 1))
    config = result.scalar_one_or_none()
    if config is None:
        config = SmtpConfig(id=1, host="", port=587, username="", password="", from_addr="", use_tls=True)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


async def update_smtp_config(db: AsyncSession, data: dict) -> SmtpConfig:
    config = await get_smtp_config(db)
    for key, value in data.items():
        setattr(config, key, value)
    await db.commit()
    await db.refresh(config)
    return config


async def get_smtp_config_dict(db: AsyncSession) -> dict:
    config = await get_smtp_config(db)
    return {
        "host": config.host,
        "port": config.port,
        "username": config.username,
        "password": config.password,
        "from_addr": config.from_addr,
        "use_tls": config.use_tls,
    }
