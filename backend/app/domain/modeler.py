"""Model training service – LightGBM baseline with leakage-safe split."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

AuditEntries = list[dict[str, str]]


def _detect_task(y: pd.Series, max_unique: int = 20) -> str:
    if y.dtype.kind in ("O", "S", "U") or isinstance(y.dtype, pd.CategoricalDtype):
        return "classification"
    if y.nunique() <= max_unique:
        return "classification"
    return "regression"


def train_baseline(
    df: pd.DataFrame,
    target_col: str,
    *,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[dict[str, Any], AuditEntries]:
    """Train LightGBM baseline, return (results_dict, audit_entries)."""
    log: AuditEntries = []

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found.")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Drop remaining non-numeric features
    non_num = X.select_dtypes(exclude="number").columns.tolist()
    if non_num:
        X = X.drop(columns=non_num)
        log.append({
            "phase": "MODELING",
            "severity": "WARNING",
            "message": f"Dropped {len(non_num)} non-numeric feature(s) before modelling: {', '.join(non_num[:5])}",
        })

    task = _detect_task(y)
    log.append({"phase": "MODELING", "severity": "INFO", "message": f"Detected task type: {task}."})

    # Label-encode target for classification
    label_map: dict | None = None
    if task == "classification" and y.dtype.kind in ("O", "S", "U"):
        label_map = {label: idx for idx, label in enumerate(sorted(y.unique()))}
        y = y.map(label_map)
        log.append({
            "phase": "MODELING",
            "severity": "ACTION",
            "message": f"Label-encoded target with {len(label_map)} classes.",
        })

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    log.append({
        "phase": "MODELING",
        "severity": "INFO",
        "message": f"Train/test split: {len(X_train)} train / {len(X_test)} test ({1 - test_size:.0%}/{test_size:.0%}).",
    })

    if task == "classification":
        model = LGBMClassifier(verbosity=-1, random_state=random_state, n_estimators=200)
    else:
        model = LGBMRegressor(verbosity=-1, random_state=random_state, n_estimators=200)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics: dict[str, Any] = {}
    if task == "classification":
        metrics["accuracy"] = round(float(accuracy_score(y_test, y_pred)), 4)
        metrics["f1_weighted"] = round(
            float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4
        )
        metrics["confusion_matrix"] = confusion_matrix(y_test, y_pred).tolist()
        log.append({
            "phase": "MODELING",
            "severity": "INFO",
            "message": f"Classification — Accuracy: {metrics['accuracy']}, F1: {metrics['f1_weighted']}.",
        })
    else:
        metrics["rmse"] = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4)
        metrics["r2"] = round(float(r2_score(y_test, y_pred)), 4)
        log.append({
            "phase": "MODELING",
            "severity": "INFO",
            "message": f"Regression — RMSE: {metrics['rmse']}, R²: {metrics['r2']}.",
        })

    importances = sorted(
        zip(X.columns.tolist(), model.feature_importances_.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )

    log.append({"phase": "MODELING", "severity": "INFO", "message": "✅ Baseline model training completed."})

    return {
        "task_type": task,
        "metrics": metrics,
        "feature_importances": [{"feature": f, "importance": i} for f, i in importances],
        "train_size": len(X_train),
        "test_size": len(X_test),
        "label_map": label_map,
    }, log
