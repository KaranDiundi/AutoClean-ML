"""Pipeline orchestration Celery task."""

from __future__ import annotations

import logging
import uuid
import traceback

import pandas as pd

from app.workers.celery_app import celery_app
from app.infrastructure.database import get_sync_session
from app.infrastructure.file_storage import FileStorage
from app.infrastructure.repositories import (
    AuditLogRepository,
    DataProfileRepository,
    DatasetRepository,
    ModelResultRepository,
    PipelineRunRepository,
)
from app.domain.profiler import DataProfiler
from app.domain.cleaner import run_cleaning_pipeline
from app.domain.engineer import run_feature_pipeline
from app.domain.modeler import train_baseline

logger = logging.getLogger("autoclean.pipeline")
storage = FileStorage()


@celery_app.task(name="execute_pipeline", bind=True, max_retries=0)
def execute_pipeline(self, run_id_str: str) -> dict:
    """Full pipeline: profile → clean → engineer → train → persist."""
    run_id = uuid.UUID(run_id_str)
    session = get_sync_session()
    all_audit: list[dict] = []

    try:
        run_repo = PipelineRunRepository(session)
        ds_repo = DatasetRepository(session)

        run = run_repo.get(run_id)
        if not run:
            raise ValueError(f"Pipeline run {run_id} not found.")

        ds = ds_repo.get(run.dataset_id)
        if not ds:
            raise ValueError(f"Dataset {run.dataset_id} not found.")

        # ── Load data ────────────────────────────────────────
        if ds.file_type == "csv":
            df = pd.read_csv(ds.filename)
        else:
            df = pd.read_parquet(ds.filename)

        target_col = run.target_column

        # ── Phase 1: Profiling ───────────────────────────────
        run_repo.update_status(run_id, "PROFILING")
        session.commit()

        profiler = DataProfiler(df)
        profile_data = profiler.profile()

        profile_repo = DataProfileRepository(session)
        profile_repo.create(
            pipeline_run_id=run_id,
            n_rows=profile_data["n_rows"],
            n_cols=profile_data["n_cols"],
            total_missing_pct=profile_data["total_missing_pct"],
            column_profiles=profile_data["columns"],
        )
        session.commit()

        # ── Phase 2: Cleaning ────────────────────────────────
        run_repo.update_status(run_id, "CLEANING")
        session.commit()

        cleaned_df, clean_logs = run_cleaning_pipeline(df, target_col)
        all_audit.extend(clean_logs)

        # Standardise target name for subsequent steps
        import re
        std_target = re.sub(r"[^a-z0-9]", "_", target_col.strip().lower())

        # ── Phase 3: Feature Engineering ─────────────────────
        run_repo.update_status(run_id, "ENGINEERING")
        session.commit()

        engineered_df, fit_params, eng_logs = run_feature_pipeline(cleaned_df, std_target)
        all_audit.extend(eng_logs)

        # ── Phase 4: Model Training ──────────────────────────
        run_repo.update_status(run_id, "TRAINING")
        session.commit()

        results, model_logs = train_baseline(engineered_df, std_target)
        all_audit.extend(model_logs)

        # ── Persist processed file ───────────────────────────
        processed_path = storage.save_bytes(
            engineered_df.to_csv(index=False).encode(),
            "processed_dataset.csv",
            prefix=f"run_{run_id_str[:8]}_",
        )

        # ── Persist model results ────────────────────────────
        model_repo = ModelResultRepository(session)
        model_repo.create(
            pipeline_run_id=run_id,
            task_type=results["task_type"],
            metrics=results["metrics"],
            feature_importances=results["feature_importances"],
            processed_file_path=processed_path,
            train_size=results["train_size"],
            test_size=results["test_size"],
        )

        # ── Persist audit logs ───────────────────────────────
        audit_repo = AuditLogRepository(session)
        audit_repo.bulk_create(
            [{"pipeline_run_id": run_id, **entry} for entry in all_audit]
        )

        run_repo.update_status(run_id, "COMPLETED", task_type=results["task_type"])
        session.commit()

        logger.info("Pipeline %s completed successfully.", run_id)
        return {"status": "COMPLETED", "run_id": str(run_id)}

    except Exception as exc:
        session.rollback()
        logger.exception("Pipeline %s failed: %s", run_id, exc)
        try:
            # Persist whatever audit entries we collected
            audit_repo = AuditLogRepository(session)
            if all_audit:
                audit_repo.bulk_create(
                    [{"pipeline_run_id": run_id, **entry} for entry in all_audit]
                )
            run_repo = PipelineRunRepository(session)
            run_repo.update_status(run_id, "FAILED", error_message=str(exc))
            session.commit()
        except Exception:
            session.rollback()
        return {"status": "FAILED", "run_id": str(run_id), "error": str(exc)}

    finally:
        session.close()
