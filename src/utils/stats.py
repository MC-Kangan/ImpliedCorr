"""Simple statistical helpers."""

from __future__ import annotations

import pandas as pd


def z_score(series: pd.Series) -> float | None:
    """Return the z-score of the latest value versus the sample."""
    clean = series.dropna()
    if len(clean) < 2:
        return None
    std = clean.std(ddof=0)
    if std == 0:
        return None
    return float((clean.iloc[-1] - clean.mean()) / std)

