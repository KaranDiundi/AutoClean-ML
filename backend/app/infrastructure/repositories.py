"""Repository layer – CRUD operations against the database."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.infrastructure.models import AuditLog, DataProfile, Dataset, ModelResult, PipelineRun


# ═════════════════════════════════════════════════════════════
# Dataset Repository
# ═════════════════════════════════════════════════════════════


class DatasetRepository:
    """Sync CRUD for datasets (used by Celery + API via sync session)."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, **kwargs: Any) -> Dataset:
        obj = Dataset(**kwargs)
        self._s.add(obj)
        self._s.flush()
        return obj

    def get(self, dataset_id: uuid.UUID) -> Dataset | None:
        return self._s.get(Dataset, dataset_id)

    def list_all(self) -> list[Dataset]:
        return list(self._s.execute(select(Dataset).order_by(Dataset.created_at.desc())).scalars())

    def delete(self, dataset_id: uuid.UUID) -> bool:
        obj = self.get(dataset_id)
        if obj:
            self._s.delete(obj)
            self._s.flush()
            return True
        return False


# ═════════════════════════════════════════════════════════════
# PipelineRun Repository
# ═════════════════════════════════════════════════════════════


class PipelineRunRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, **kwargs: Any) -> PipelineRun:
        obj = PipelineRun(**kwargs)
        self._s.add(obj)
        self._s.flush()
        return obj

    def get(self, run_id: uuid.UUID) -> PipelineRun | None:
        return self._s.get(PipelineRun, run_id)

    def update_status(
        self,
        run_id: uuid.UUID,
        status: str,
        *,
        error_message: str | None = None,
        task_type: str | None = None,
    ) -> None:
        values: dict[str, Any] = {"status": status}
        if status == "PROFILING":
            values["started_at"] = datetime.now(timezone.utc)
        if status in ("COMPLETED", "FAILED"):
            values["completed_at"] = datetime.now(timezone.utc)
        if error_message:
            values["error_message"] = error_message
        if task_type:
            values["task_type"] = task_type
        self._s.execute(update(PipelineRun).where(PipelineRun.id == run_id).values(**values))
        self._s.flush()

    def list_by_dataset(self, dataset_id: uuid.UUID) -> list[PipelineRun]:
        return list(
            self._s.execute(
                select(PipelineRun)
                .where(PipelineRun.dataset_id == dataset_id)
                .order_by(PipelineRun.started_at.desc())
            ).scalars()
        )


# ═════════════════════════════════════════════════════════════
# DataProfile Repository
# ═════════════════════════════════════════════════════════════


class DataProfileRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, **kwargs: Any) -> DataProfile:
        obj = DataProfile(**kwargs)
        self._s.add(obj)
        self._s.flush()
        return obj

    def get_by_run(self, run_id: uuid.UUID) -> DataProfile | None:
        return self._s.execute(
            select(DataProfile).where(DataProfile.pipeline_run_id == run_id)
        ).scalar_one_or_none()


# ═════════════════════════════════════════════════════════════
# AuditLog Repository
# ═════════════════════════════════════════════════════════════


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def bulk_create(self, entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            self._s.add(AuditLog(**entry))
        self._s.flush()

    def list_by_run(self, run_id: uuid.UUID) -> list[AuditLog]:
        return list(
            self._s.execute(
                select(AuditLog)
                .where(AuditLog.pipeline_run_id == run_id)
                .order_by(AuditLog.created_at.asc())
            ).scalars()
        )


# ═════════════════════════════════════════════════════════════
# ModelResult Repository
# ═════════════════════════════════════════════════════════════


class ModelResultRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, **kwargs: Any) -> ModelResult:
        obj = ModelResult(**kwargs)
        self._s.add(obj)
        self._s.flush()
        return obj

    def get_by_run(self, run_id: uuid.UUID) -> ModelResult | None:
        return self._s.execute(
            select(ModelResult).where(ModelResult.pipeline_run_id == run_id)
        ).scalar_one_or_none()
