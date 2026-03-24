"""Unit tests for domain services."""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from app.domain.profiler import DataProfiler
from app.domain.cleaner import run_cleaning_pipeline
from app.domain.engineer import run_feature_pipeline
from app.domain.modeler import train_baseline


class TestProfiler:
    def test_basic_profile(self, sample_df: pd.DataFrame):
        profile = DataProfiler(sample_df).profile()
        assert profile["n_rows"] == 100
        assert profile["n_cols"] == 8
        assert len(profile["columns"]) == 8
        assert profile["total_missing_pct"] > 0

    def test_column_categories(self, sample_df: pd.DataFrame):
        profile = DataProfiler(sample_df).profile()
        cats = {c["name"]: c["category"] for c in profile["columns"]}
        assert cats["Age"] == "numeric"
        assert cats["Income"] == "numeric"
        assert cats["Category"] == "categorical"


class TestCleaner:
    def test_standardises_columns(self, sample_df: pd.DataFrame):
        cleaned, logs = run_cleaning_pipeline(sample_df, "Target")
        assert all(c == c.lower() for c in cleaned.columns)
        assert all(" " not in c for c in cleaned.columns)

    def test_drops_id_column(self, sample_df: pd.DataFrame):
        cleaned, logs = run_cleaning_pipeline(sample_df, "Target")
        assert "id" not in cleaned.columns

    def test_imputes_missing(self, sample_df: pd.DataFrame):
        cleaned, logs = run_cleaning_pipeline(sample_df, "Target")
        assert cleaned.drop(columns=["target"]).isnull().sum().sum() == 0

    def test_clips_outliers(self, sample_df: pd.DataFrame):
        cleaned, logs = run_cleaning_pipeline(sample_df, "Target")
        # After standardisation, column is lowercase
        assert "income" in cleaned.columns
        assert cleaned["income"].max() < 999999

    def test_returns_audit_entries(self, sample_df: pd.DataFrame):
        _, logs = run_cleaning_pipeline(sample_df, "Target")
        assert len(logs) > 0
        assert all("phase" in e and "message" in e for e in logs)


class TestEngineer:
    def test_datetime_extraction(self, sample_df: pd.DataFrame):
        cleaned, _ = run_cleaning_pipeline(sample_df, "Target")
        engineered, _, logs = run_feature_pipeline(cleaned, "target")
        # 'Join Date' → standardised to 'join_date' → parsed → 'join_date_year' etc.
        date_cols = [c for c in engineered.columns if "join" in c and ("year" in c or "month" in c)]
        assert len(date_cols) > 0, f"Expected datetime columns, got: {list(engineered.columns)}"

    def test_encodes_categoricals(self, sample_df: pd.DataFrame):
        cleaned, _ = run_cleaning_pipeline(sample_df, "Target")
        engineered, _, _ = run_feature_pipeline(cleaned, "target")
        # No object columns left (except target)
        obj_cols = [c for c in engineered.select_dtypes("object").columns if c != "target"]
        assert len(obj_cols) == 0

    def test_drops_zero_variance(self, sample_df: pd.DataFrame):
        cleaned, _ = run_cleaning_pipeline(sample_df, "Target")
        engineered, _, logs = run_feature_pipeline(cleaned, "target")
        assert "constant_col" not in engineered.columns


class TestModeler:
    def test_classification_task(self, sample_df: pd.DataFrame):
        cleaned, _ = run_cleaning_pipeline(sample_df, "Target")
        engineered, _, _ = run_feature_pipeline(cleaned, "target")
        results, logs = train_baseline(engineered, "target")
        assert results["task_type"] == "classification"
        assert "accuracy" in results["metrics"]
        assert "f1_weighted" in results["metrics"]
        assert len(results["feature_importances"]) > 0

    def test_regression_task(self):
        np.random.seed(42)
        df = pd.DataFrame({
            "x1": np.random.randn(100),
            "x2": np.random.randn(100),
            "target": np.random.randn(100) * 100,
        })
        results, logs = train_baseline(df, "target")
        assert results["task_type"] == "regression"
        assert "rmse" in results["metrics"]
        assert "r2" in results["metrics"]
