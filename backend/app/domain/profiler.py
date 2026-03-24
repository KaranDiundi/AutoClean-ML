"""Data profiling service – pure business logic, no framework deps."""

from __future__ import annotations

from typing import Any

import pandas as pd


class DataProfiler:
    """Compute comprehensive metadata for a DataFrame."""

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    @staticmethod
    def _categorise_dtype(dtype: Any) -> str:
        kind = dtype.kind
        if kind in ("i", "u", "f"):
            return "numeric"
        if kind == "b":
            return "boolean"
        if kind in ("M", "m"):
            return "datetime"
        if kind in ("O", "S", "U"):
            return "categorical"
        return "other"

    def profile(self) -> dict[str, Any]:
        """Return a dict with dataset-level and column-level metadata."""
        df = self._df
        n_rows, n_cols = df.shape
        total_cells = n_rows * n_cols
        total_missing = int(df.isnull().sum().sum())

        columns: list[dict[str, Any]] = []
        for col in df.columns:
            s = df[col]
            miss = int(s.isnull().sum())
            info: dict[str, Any] = {
                "name": col,
                "dtype": str(s.dtype),
                "category": self._categorise_dtype(s.dtype),
                "missing_count": miss,
                "missing_pct": round(miss / n_rows * 100, 2) if n_rows else 0.0,
                "n_unique": int(s.nunique()),
            }
            # Add numeric stats
            if info["category"] == "numeric":
                info["mean"] = round(float(s.mean()), 4) if miss < n_rows else None
                info["std"] = round(float(s.std()), 4) if miss < n_rows else None
                info["min"] = round(float(s.min()), 4) if miss < n_rows else None
                info["max"] = round(float(s.max()), 4) if miss < n_rows else None
            columns.append(info)

        return {
            "n_rows": n_rows,
            "n_cols": n_cols,
            "total_missing_pct": round(total_missing / total_cells * 100, 2) if total_cells else 0,
            "columns": columns,
        }
