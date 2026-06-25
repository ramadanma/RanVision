import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, faces, records, report_configs, rules, sources, stream, zones
from app.services.hls_service import hls_manager
from app.services.redis_service import close_redis
from app.worker.worker_manager import worker_manager

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Restore sources that were active before last restart
    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.source import Source
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Source).where(Source.is_active == True))
            active_sources = result.scalars().all()
        for source in active_sources:
            try:
                hls_manager.start(source)
                worker_manager.start(source.id, source.user_id)
                logging.getLogger(__name__).info("Restored source %d on startup", source.id)
            except Exception as e:
                logging.getLogger(__name__).warning("Failed to restore source %d: %s", source.id, e)
    except Exception as e:
        logging.getLogger(__name__).warning("Startup restore failed: %s", e)

    yield

    # Graceful shutdown
    hls_manager.stop_all()
    worker_manager.stop_all()
    await close_redis()


app = FastAPI(title="RanVision API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"

app.include_router(auth.router, prefix=PREFIX)
app.include_router(sources.router, prefix=PREFIX)
app.include_router(stream.router, prefix=PREFIX)
app.include_router(zones.router, prefix=PREFIX)
app.include_router(rules.router, prefix=PREFIX)
app.include_router(faces.router, prefix=PREFIX)
app.include_router(report_configs.router, prefix=PREFIX)
app.include_router(records.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}
