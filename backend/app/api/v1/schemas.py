"""Pydantic request / response schemas – strict type safety."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ═════════════════════════════════════════════════════════════
# Dataset Schemas
# ═════════════════════════════════════════════════════════════


class DatasetOut(BaseModel):
    id: uuid.UUID
    filename: str
    original_name: str
    file_type: str
    file_size_bytes: int
    row_count: int | None = None
    column_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetListOut(BaseModel):
    datasets: list[DatasetOut]


# ═════════════════════════════════════════════════════════════
# Pipeline Schemas
# ═════════════════════════════════════════════════════════════


class PipelineRunRequest(BaseModel):
    dataset_id: uuid.UUID
    target_column: str = Field(..., min_length=1)


class PipelineRunOut(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    target_column: str
    status: str
    task_type: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: int
    phase: str
    severity: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    category: str
    missing_count: int
    missing_pct: float
    n_unique: int
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None


class DataProfileOut(BaseModel):
    n_rows: int
    n_cols: int
    total_missing_pct: float
    columns: list[ColumnProfile]


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class ModelResultOut(BaseModel):
    task_type: str
    metrics: dict[str, Any]
    feature_importances: list[FeatureImportance]
    train_size: int
    test_size: int

    model_config = {"from_attributes": True}


class PipelineResultsOut(BaseModel):
    run: PipelineRunOut
    profile: DataProfileOut | None = None
    model_result: ModelResultOut | None = None
    audit_logs: list[AuditLogOut] = []
