"""Data cleaning pipeline – pure domain logic."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd


AuditEntries = list[dict[str, str]]


def _standardise_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", name.strip().lower())


def run_cleaning_pipeline(
    df: pd.DataFrame,
    target_col: str,
    *,
    missing_threshold: float = 0.50,
    iqr_multiplier: float = 1.5,
) -> tuple[pd.DataFrame, AuditEntries]:
    """Execute full cleaning pipeline, return (cleaned_df, audit_entries).

    Every audit entry is ``{"phase": "CLEANING", "severity": ..., "message": ...}``.
    """
    df = df.copy()
    log: AuditEntries = []

    # ── Column standardisation ──────────────────────────────
    original = list(df.columns)
    df.columns = [_standardise_name(c) for c in df.columns]
    renamed = {o: n for o, n in zip(original, df.columns) if o != n}
    if renamed:
        log.append({
            "phase": "CLEANING",
            "severity": "ACTION",
            "message": (
                f"Standardised {len(renamed)} column name(s): "
                + ", ".join(f"'{o}' → '{n}'" for o, n in list(renamed.items())[:5])
                + ("…" if len(renamed) > 5 else "")
            ),
        })

    target_col = _standardise_name(target_col)

    # ── Drop high-missing columns ───────────────────────────
    miss_frac = df.isnull().mean()
    to_drop = [c for c in miss_frac.index if miss_frac[c] > missing_threshold and c != target_col]
    if to_drop:
        df = df.drop(columns=to_drop)
        for c in to_drop:
            log.append({
                "phase": "CLEANING",
                "severity": "WARNING",
                "message": f"Dropped column '{c}' — {miss_frac[c]:.1%} missing (threshold {missing_threshold:.0%}).",
            })

    # ── Drop ID-like columns ────────────────────────────────
    # Only consider integer columns (skip floats, strings, dates)
    n = len(df)
    if n > 0:
        id_cols = [
            c for c in df.columns
            if c != target_col
            and df[c].nunique() == n
            and df[c].dtype.kind in ("i", "u")
        ]
        if id_cols:
            df = df.drop(columns=id_cols)
            for c in id_cols:
                log.append({
                    "phase": "CLEANING",
                    "severity": "ACTION",
                    "message": f"Dropped column '{c}' — 100% unique values (likely ID).",
                })

    # ── Impute missing values ───────────────────────────────
    for col in df.columns:
        if col == target_col:
            continue
        n_miss = int(df[col].isnull().sum())
        if n_miss == 0:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            median = df[col].median()
            df[col] = df[col].fillna(median)
            log.append({
                "phase": "CLEANING",
                "severity": "ACTION",
                "message": f"Imputed {n_miss} missing value(s) in '{col}' with median ({median:.4g}).",
            })
        else:
            mode_vals = df[col].mode()
            if len(mode_vals) > 0:
                mode = mode_vals.iloc[0]
                df[col] = df[col].fillna(mode)
                log.append({
                    "phase": "CLEANING",
                    "severity": "ACTION",
                    "message": f"Imputed {n_miss} missing value(s) in '{col}' with mode ('{mode}').",
                })

    # ── Clip outliers (IQR) ──────────────────────────────────
    for col in df.select_dtypes(include="number").columns:
        if col == target_col:
            continue
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower, upper = q1 - iqr_multiplier * iqr, q3 + iqr_multiplier * iqr
        n_clip = int(((df[col] < lower) | (df[col] > upper)).sum())
        if n_clip > 0:
            df[col] = df[col].clip(lower=lower, upper=upper)
            log.append({
                "phase": "CLEANING",
                "severity": "ACTION",
                "message": f"Clipped {n_clip} outlier(s) in '{col}' to [{lower:.4g}, {upper:.4g}] (IQR×{iqr_multiplier}).",
            })

    log.append({"phase": "CLEANING", "severity": "INFO", "message": "✅ Cleaning pipeline completed."})
    return df, log
