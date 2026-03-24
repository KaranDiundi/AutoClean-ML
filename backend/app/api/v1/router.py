"""Aggregated v1 API router."""

from fastapi import APIRouter

from app.api.v1.datasets import router as datasets_router
from app.api.v1.pipelines import router as pipelines_router

router = APIRouter()
router.include_router(datasets_router)
router.include_router(pipelines_router)
