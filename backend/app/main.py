"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware import register_middleware
from app.api.v1.router import router as v1_router
from app.config import settings
from app.infrastructure.database import sync_engine
from app.infrastructure.models import Base

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev convenience), do nothing on shutdown."""
    Base.metadata.create_all(bind=sync_engine)
    yield


app = FastAPI(
    title="AutoClean API",
    description="Enterprise-grade autonomous data cleaning & feature engineering",
    version="1.0.0",
    lifespan=lifespan,
)

register_middleware(app)
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
