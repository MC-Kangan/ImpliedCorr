"""Implied correlation calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import EPSILON
from src.analytics.correlation import align_weights, compute_constant_correlation_series


def compute_implied_correlation_history(
    basket_vol: pd.Series,
    constituent_vols: pd.DataFrame,
    weights: pd.Series,
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Compute historical implied correlation using full and approximate formulas."""
    vols = constituent_vols.astype(float)
    common_weights = align_weights(weights, vols.columns)
    weights_row = common_weights.to_numpy(dtype=float)
    approx_denominator = (vols.pow(2) * weights_row).sum(axis=1)

    result = compute_constant_correlation_series(
        basket_vol=basket_vol,
        constituent_vols=vols,
        weights=weights,
        epsilon=epsilon,
        clip=False,
        column_name="rho_imp_full",
    )

    rho_approx = pd.Series(np.nan, index=vols.index, name="rho_imp_approx")
    approx_mask = approx_denominator.abs() > epsilon
    rho_approx.loc[approx_mask] = result.loc[approx_mask, "basket_variance"] / approx_denominator.loc[approx_mask]

    result["basket_implied_vol"] = basket_vol
    result["weighted_constituent_variance"] = (vols.pow(2) * weights_row).sum(axis=1)
    result["single_name_variance_term"] = result["diag_term"]
    result["rho_imp_approx"] = rho_approx
    result["constituent_count"] = vols.notna().sum(axis=1)
    result["rho_out_of_bounds"] = result["rho_imp_full"].lt(-1.0) | result["rho_imp_full"].gt(1.0)
    result.index.name = "date"
    return result


def current_percentile(series: pd.Series) -> float | None:
    """Return the percentile rank of the latest value in the historical sample."""
    clean = series.dropna()
    if clean.empty:
        return None
    latest = clean.iloc[-1]
    return float((clean <= latest).mean())
