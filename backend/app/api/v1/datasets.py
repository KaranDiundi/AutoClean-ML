"""Dataset API routes – upload, list, delete."""

from __future__ import annotations

import uuid

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, status

from app.api.v1.schemas import DatasetListOut, DatasetOut
from app.infrastructure.database import get_sync_session
from app.infrastructure.file_storage import FileStorage
from app.infrastructure.repositories import DatasetRepository

router = APIRouter(prefix="/datasets", tags=["datasets"])
storage = FileStorage()


@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(file: UploadFile = File(...)) -> DatasetOut:
    """Upload a CSV or Parquet file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("csv", "parquet"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    contents = await file.read()
    stored_path = storage.save_bytes(contents, file.filename)

    # Quick row/col count
    try:
        if ext == "csv":
            df = pd.read_csv(stored_path)
        else:
            df = pd.read_parquet(stored_path)
        row_count, col_count = df.shape
    except Exception as e:
        storage.delete(stored_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    session = get_sync_session()
    try:
        repo = DatasetRepository(session)
        ds = repo.create(
            filename=stored_path,
            original_name=file.filename,
            file_type=ext,
            file_size_bytes=len(contents),
            row_count=row_count,
            column_count=col_count,
        )
        session.commit()
        return DatasetOut.model_validate(ds)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.get("", response_model=DatasetListOut)
async def list_datasets() -> DatasetListOut:
    session = get_sync_session()
    try:
        repo = DatasetRepository(session)
        datasets = repo.list_all()
        return DatasetListOut(datasets=[DatasetOut.model_validate(d) for d in datasets])
    finally:
        session.close()


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset(dataset_id: uuid.UUID) -> DatasetOut:
    session = get_sync_session()
    try:
        repo = DatasetRepository(session)
        ds = repo.get(dataset_id)
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found.")
        return DatasetOut.model_validate(ds)
    finally:
        session.close()


@router.get("/{dataset_id}/columns")
async def get_columns(dataset_id: uuid.UUID) -> dict:
    """Return column names for target variable selection."""
    session = get_sync_session()
    try:
        repo = DatasetRepository(session)
        ds = repo.get(dataset_id)
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found.")

        if ds.file_type == "csv":
            df = pd.read_csv(ds.filename, nrows=0)
        else:
            df = pd.read_parquet(ds.filename).head(0)

        return {"columns": df.columns.tolist()}
    finally:
        session.close()


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: uuid.UUID) -> None:
    session = get_sync_session()
    try:
        repo = DatasetRepository(session)
        ds = repo.get(dataset_id)
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found.")
        storage.delete(ds.filename)
        repo.delete(dataset_id)
        session.commit()
    except HTTPException:
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
