"""Constituent contribution calculations."""

from __future__ import annotations

import pandas as pd


def compute_latest_contributions(
    constituent_vols: pd.DataFrame,
    weights: pd.Series,
) -> pd.DataFrame:
    """Compute constituent-level contribution diagnostics for the latest date."""
    latest_date = constituent_vols.dropna(how="all").index.max()
    if pd.isna(latest_date):
        return pd.DataFrame()

    latest_vols = constituent_vols.loc[latest_date].dropna()
    aligned_weights = weights.reindex(latest_vols.index)

    frame = pd.DataFrame(
        {
            "ticker": latest_vols.index,
            "weight": aligned_weights.to_numpy(),
            "implied_vol": latest_vols.to_numpy(),
        }
    )
    frame["weighted_variance_contribution"] = frame["weight"].pow(2) * frame["implied_vol"].pow(2)
    frame["weighted_vol_proxy"] = frame["weight"] * frame["implied_vol"]
    variance_total = frame["weighted_variance_contribution"].sum()
    frame["variance_contribution_pct"] = (
        frame["weighted_variance_contribution"] / variance_total if variance_total > 0 else 0.0
    )
    frame["latest_date"] = latest_date
    return frame.sort_values("weighted_variance_contribution", ascending=False).reset_index(drop=True)

