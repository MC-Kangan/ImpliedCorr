"""Implied correlation calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import EPSILON


def _ordered_cross_term(weighted_vols: pd.DataFrame, weighted_variance_term: pd.Series) -> pd.Series:
    weighted_sum_sq = weighted_vols.sum(axis=1).pow(2)
    return weighted_sum_sq - weighted_variance_term


def compute_implied_correlation_history(
    basket_vol: pd.Series,
    constituent_vols: pd.DataFrame,
    weights: pd.Series,
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Compute historical implied correlation using full and approximate formulas."""
    common_weights = weights.reindex(constituent_vols.columns)
    if common_weights.isna().any():
        missing = ", ".join(common_weights[common_weights.isna()].index.tolist())
        raise ValueError(f"Weights missing for tickers: {missing}")

    weights_row = common_weights.to_numpy(dtype=float)
    vols = constituent_vols.astype(float)

    weighted_variance_term = (vols.pow(2) * np.square(weights_row)).sum(axis=1)
    weighted_vol_proxy = (vols * weights_row).sum(axis=1)
    cross_term = _ordered_cross_term(vols * weights_row, weighted_variance_term)
    approx_denominator = (vols.pow(2) * weights_row).sum(axis=1)
    basket_variance = basket_vol.astype(float).pow(2)

    rho_full = pd.Series(np.nan, index=vols.index, name="rho_imp_full")
    stable_mask = cross_term.abs() > epsilon
    rho_full.loc[stable_mask] = (basket_variance.loc[stable_mask] - weighted_variance_term.loc[stable_mask]) / cross_term.loc[
        stable_mask
    ]

    rho_approx = pd.Series(np.nan, index=vols.index, name="rho_imp_approx")
    approx_mask = approx_denominator.abs() > epsilon
    rho_approx.loc[approx_mask] = basket_variance.loc[approx_mask] / approx_denominator.loc[approx_mask]

    result = pd.DataFrame(
        {
            "basket_implied_vol": basket_vol,
            "basket_variance": basket_variance,
            "weighted_constituent_vol": weighted_vol_proxy,
            "weighted_constituent_variance": (vols.pow(2) * weights_row).sum(axis=1),
            "single_name_variance_term": weighted_variance_term,
            "cross_term": cross_term,
            "rho_imp_full": rho_full,
            "rho_imp_approx": rho_approx,
            "constituent_count": vols.notna().sum(axis=1),
            "denominator_small": ~stable_mask,
            "rho_out_of_bounds": rho_full.lt(-1.0) | rho_full.gt(1.0),
        }
    )
    result.index.name = "date"
    return result


def current_percentile(series: pd.Series) -> float | None:
    """Return the percentile rank of the latest value in the historical sample."""
    clean = series.dropna()
    if clean.empty:
        return None
    latest = clean.iloc[-1]
    return float((clean <= latest).mean())

