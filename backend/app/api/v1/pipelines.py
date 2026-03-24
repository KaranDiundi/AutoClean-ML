"""Pipeline API routes – trigger, status, results, download."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from app.api.v1.schemas import (
    AuditLogOut,
    ColumnProfile,
    DataProfileOut,
    FeatureImportance,
    ModelResultOut,
    PipelineResultsOut,
    PipelineRunOut,
    PipelineRunRequest,
)
from app.infrastructure.database import get_sync_session
from app.infrastructure.repositories import (
    AuditLogRepository,
    DataProfileRepository,
    DatasetRepository,
    ModelResultRepository,
    PipelineRunRepository,
)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post("/run", response_model=PipelineRunOut, status_code=status.HTTP_202_ACCEPTED)
async def trigger_pipeline(body: PipelineRunRequest) -> PipelineRunOut:
    """Create a pipeline run and dispatch to Celery."""
    session = get_sync_session()
    try:
        ds_repo = DatasetRepository(session)
        ds = ds_repo.get(body.dataset_id)
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found.")

        run_repo = PipelineRunRepository(session)
        run = run_repo.create(
            dataset_id=body.dataset_id,
            target_column=body.target_column,
        )
        session.commit()

        # Dispatch Celery task
        from app.workers.pipeline_task import execute_pipeline

        execute_pipeline.delay(str(run.id))

        return PipelineRunOut.model_validate(run)
    except HTTPException:
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.get("/{run_id}/status")
async def stream_status(run_id: uuid.UUID) -> EventSourceResponse:
    """SSE endpoint — streams pipeline status updates until COMPLETED or FAILED."""

    async def event_generator():
        prev_status = ""
        for _ in range(600):  # max ~5 min
            session = get_sync_session()
            try:
                repo = PipelineRunRepository(session)
                run = repo.get(run_id)
                if not run:
                    yield {"event": "error", "data": "Run not found"}
                    return
                if run.status != prev_status:
                    prev_status = run.status
                    yield {
                        "event": "status",
                        "data": json.dumps({
                            "status": run.status,
                            "task_type": run.task_type,
                            "error_message": run.error_message,
                        }),
                    }
                if run.status in ("COMPLETED", "FAILED"):
                    return
            finally:
                session.close()
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@router.get("/{run_id}/results", response_model=PipelineResultsOut)
async def get_results(run_id: uuid.UUID) -> PipelineResultsOut:
    """Return full pipeline results: profile, model metrics, audit log."""
    session = get_sync_session()
    try:
        run_repo = PipelineRunRepository(session)
        run = run_repo.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Pipeline run not found.")

        profile_repo = DataProfileRepository(session)
        profile_row = profile_repo.get_by_run(run_id)
        profile_out = None
        if profile_row:
            profile_out = DataProfileOut(
                n_rows=profile_row.n_rows,
                n_cols=profile_row.n_cols,
                total_missing_pct=profile_row.total_missing_pct,
                columns=[ColumnProfile(**c) for c in profile_row.column_profiles],
            )

        model_repo = ModelResultRepository(session)
        model_row = model_repo.get_by_run(run_id)
        model_out = None
        if model_row:
            model_out = ModelResultOut(
                task_type=model_row.task_type,
                metrics=model_row.metrics,
                feature_importances=[
                    FeatureImportance(**fi) for fi in model_row.feature_importances
                ],
                train_size=model_row.train_size,
                test_size=model_row.test_size,
            )

        audit_repo = AuditLogRepository(session)
        audit_rows = audit_repo.list_by_run(run_id)

        return PipelineResultsOut(
            run=PipelineRunOut.model_validate(run),
            profile=profile_out,
            model_result=model_out,
            audit_logs=[AuditLogOut.model_validate(a) for a in audit_rows],
        )
    finally:
        session.close()


@router.get("/{run_id}/download")
async def download_processed(run_id: uuid.UUID) -> FileResponse:
    """Download the processed CSV."""
    session = get_sync_session()
    try:
        model_repo = ModelResultRepository(session)
        result = model_repo.get_by_run(run_id)
        if not result or not result.processed_file_path:
            raise HTTPException(status_code=404, detail="Processed file not found.")
        return FileResponse(
            result.processed_file_path,
            media_type="text/csv",
            filename="processed_dataset.csv",
        )
    finally:
        session.close()
