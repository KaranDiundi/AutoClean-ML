"""Test fixtures."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Return a small DataFrame with mixed types, missing values, and outliers."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "ID": range(1, n + 1),
        "Age": np.random.randint(18, 75, n).astype(float),
        "Income": np.random.normal(55000, 15000, n),
        "Category": np.random.choice(["A", "B", "C", "D"], n),
        "City": np.random.choice([f"City_{i}" for i in range(25)], n),
        "Join Date": pd.date_range("2020-01-01", periods=n, freq="D").astype(str),
        "Constant_Col": "same_value",
        "Target": np.random.choice(["Yes", "No"], n),
    })
    # Inject missing values
    df.loc[0:4, "Age"] = np.nan
    df.loc[5:9, "Category"] = np.nan
    # Inject outlier
    df.loc[0, "Income"] = 999999
    return df
