"""Feature engineering pipeline – pure domain logic."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

AuditEntries = list[dict[str, str]]


def run_feature_pipeline(
    df: pd.DataFrame,
    target_col: str,
    *,
    ohe_threshold: int = 10,
    corr_threshold: float = 0.95,
) -> tuple[pd.DataFrame, dict[str, Any], AuditEntries]:
    """Execute feature engineering, return (df, fit_params, audit_entries)."""
    df = df.copy()
    log: AuditEntries = []
    fit_params: dict[str, Any] = {}

    df, dt_cols, dt_logs = _extract_datetime(df, target_col)
    log.extend(dt_logs)
    fit_params["datetime_cols"] = dt_cols

    df, ohe_cols, freq_maps, enc_logs = _encode_categoricals(df, target_col, ohe_threshold)
    log.extend(enc_logs)
    fit_params["ohe_cols"] = ohe_cols
    fit_params["freq_maps"] = freq_maps

    df, zv_cols, zv_logs = _drop_zero_variance(df, target_col)
    log.extend(zv_logs)
    fit_params["zero_var_cols"] = zv_cols

    df, hc_cols, hc_logs = _drop_high_correlation(df, target_col, corr_threshold)
    log.extend(hc_logs)
    fit_params["high_corr_cols"] = hc_cols

    log.append({"phase": "ENGINEERING", "severity": "INFO", "message": "✅ Feature engineering completed."})
    return df, fit_params, log


# ── Internal helpers ─────────────────────────────────────────


def _extract_datetime(
    df: pd.DataFrame, target: str
) -> tuple[pd.DataFrame, list[str], AuditEntries]:
    dt_cols: list[str] = []
    log: AuditEntries = []

    for col in df.select_dtypes(include=["object", "string"]).columns:
        if col == target:
            continue
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().mean() >= 0.70:
                dt_cols.append(col)
                df[f"{col}_year"] = parsed.dt.year
                df[f"{col}_month"] = parsed.dt.month
                df[f"{col}_day"] = parsed.dt.day
                df[f"{col}_dayofweek"] = parsed.dt.dayofweek
                df = df.drop(columns=[col])
                log.append({
                    "phase": "ENGINEERING",
                    "severity": "ACTION",
                    "message": f"Parsed '{col}' as datetime → extracted year/month/day/dayofweek.",
                })
        except Exception:
            continue

    for col in df.select_dtypes(include=["datetime", "datetimetz"]).columns:
        if col == target:
            continue
        dt_cols.append(col)
        df[f"{col}_year"] = df[col].dt.year
        df[f"{col}_month"] = df[col].dt.month
        df[f"{col}_day"] = df[col].dt.day
        df[f"{col}_dayofweek"] = df[col].dt.dayofweek
        df = df.drop(columns=[col])
        log.append({
            "phase": "ENGINEERING",
            "severity": "ACTION",
            "message": f"Extracted datetime components from '{col}'.",
        })

    return df, dt_cols, log


def _encode_categoricals(
    df: pd.DataFrame, target: str, ohe_threshold: int
) -> tuple[pd.DataFrame, list[str], dict[str, dict], AuditEntries]:
    cat_cols = [
        c for c in df.select_dtypes(include=["object", "string", "category"]).columns if c != target
    ]
    ohe_cols: list[str] = []
    freq_maps: dict[str, dict] = {}
    log: AuditEntries = []

    for col in cat_cols:
        n_unique = df[col].nunique()
        if n_unique < ohe_threshold:
            ohe_cols.append(col)
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True, dtype=int)
            df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
            log.append({
                "phase": "ENGINEERING",
                "severity": "ACTION",
                "message": f"One-Hot encoded '{col}' ({n_unique} unique) → {dummies.shape[1]} dummy column(s).",
            })
        else:
            fm = df[col].value_counts().to_dict()
            freq_maps[col] = fm
            df[col] = df[col].map(fm).fillna(0).astype(int)
            log.append({
                "phase": "ENGINEERING",
                "severity": "ACTION",
                "message": f"Frequency-encoded '{col}' ({n_unique} unique values).",
            })

    return df, ohe_cols, freq_maps, log


def _drop_zero_variance(
    df: pd.DataFrame, target: str
) -> tuple[pd.DataFrame, list[str], AuditEntries]:
    to_drop = [c for c in df.columns if c != target and df[c].nunique() <= 1]
    log: AuditEntries = []
    if to_drop:
        df = df.drop(columns=to_drop)
        for c in to_drop:
            log.append({
                "phase": "ENGINEERING",
                "severity": "ACTION",
                "message": f"Dropped zero-variance column '{c}'.",
            })
    return df, to_drop, log


def _drop_high_correlation(
    df: pd.DataFrame, target: str, threshold: float
) -> tuple[pd.DataFrame, list[str], AuditEntries]:
    numeric = [c for c in df.select_dtypes(include="number").columns if c != target]
    log: AuditEntries = []
    if len(numeric) < 2:
        return df, [], log

    corr = df[numeric].corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1))
    to_drop = [col for col in upper.columns if any(upper[col] > threshold)]
    to_drop = [c for c in to_drop if c != target]

    if to_drop:
        df = df.drop(columns=to_drop)
        for c in to_drop:
            log.append({
                "phase": "ENGINEERING",
                "severity": "ACTION",
                "message": f"Dropped highly-correlated column '{c}' (|r| > {threshold}).",
            })

    return df, to_drop, log
