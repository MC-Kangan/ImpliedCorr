"""Realized correlation calculations from dividend-adjusted realized vol series."""

from __future__ import annotations

import pandas as pd

from src.config import EPSILON
from src.analytics.correlation import compute_constant_correlation_series


def compute_realized_correlation_history(
    basket_rvol: pd.Series,
    constituent_rvols: pd.DataFrame,
    weights: pd.Series,
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Back out average realized correlation from basket and constituent realized vols."""
    history = compute_constant_correlation_series(
        basket_vol=basket_rvol,
        constituent_vols=constituent_rvols.astype(float),
        weights=weights,
        epsilon=epsilon,
        clip=True,
        column_name="rho_realized",
    )
    history = history.rename(
        columns={
            "weighted_constituent_vol": "weighted_constituent_rvol",
            "diag_term": "realized_diag_term",
            "cross_term": "realized_cross_term",
            "basket_variance": "realized_basket_variance",
            "denominator_small": "realized_denominator_small",
        }
    )
    history["realized_basket_vol"] = basket_rvol
    history["realized_single_name_variance_term"] = history["realized_diag_term"]
    history.index.name = "date"
    return history.sort_index()
