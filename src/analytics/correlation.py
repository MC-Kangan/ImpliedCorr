"""Shared constant-correlation analytics helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import EPSILON


def align_weights(weights: pd.Series, columns: pd.Index) -> pd.Series:
    """Align a weight vector to frame columns and validate completeness."""
    common_weights = weights.reindex(columns)
    if common_weights.isna().any():
        missing = ", ".join(common_weights[common_weights.isna()].index.tolist())
        raise ValueError(f"Weights missing for tickers: {missing}")
    return common_weights.astype(float)


def compute_variance_terms(
    constituent_vols: pd.DataFrame,
    weights: pd.Series,
) -> pd.DataFrame:
    """Compute weighted vol, diagonal variance term, and cross term."""
    aligned_weights = align_weights(weights, constituent_vols.columns)
    weight_row = aligned_weights.to_numpy(dtype=float)
    vols = constituent_vols.astype(float)

    weighted_constituent_vol = (vols * weight_row).sum(axis=1)
    diag_term = (vols.pow(2) * np.square(weight_row)).sum(axis=1)
    cross_term = weighted_constituent_vol.pow(2) - diag_term

    return pd.DataFrame(
        {
            "weighted_constituent_vol": weighted_constituent_vol,
            "diag_term": diag_term,
            "cross_term": cross_term,
        },
        index=vols.index,
    )


def compute_constant_correlation_series(
    basket_vol: pd.Series,
    constituent_vols: pd.DataFrame,
    weights: pd.Series,
    epsilon: float = EPSILON,
    clip: bool = False,
    column_name: str = "correlation",
) -> pd.DataFrame:
    """Back out a constant average correlation from the basket variance identity."""
    variance_terms = compute_variance_terms(constituent_vols=constituent_vols, weights=weights)
    basket_variance = basket_vol.astype(float).pow(2)
    stable_mask = variance_terms["cross_term"].abs() > epsilon

    correlation = pd.Series(np.nan, index=constituent_vols.index, name=column_name)
    correlation.loc[stable_mask] = (
        basket_variance.loc[stable_mask] - variance_terms.loc[stable_mask, "diag_term"]
    ) / variance_terms.loc[stable_mask, "cross_term"]
    if clip:
        correlation = correlation.clip(-1.0, 1.0)

    result = variance_terms.copy()
    result["basket_variance"] = basket_variance
    result[column_name] = correlation
    result["denominator_small"] = ~stable_mask
    result.index.name = "date"
    return result


def compute_log_return_correlation_matrix(prices: pd.DataFrame, forward_fill: bool = True) -> pd.DataFrame:
    """Compute a constituent log-return correlation matrix from price history."""
    price_frame = prices.sort_index().copy()
    if forward_fill:
        price_frame = price_frame.ffill()
    returns = np.log(price_frame / price_frame.shift(1))
    returns = returns.dropna(how="all").dropna(axis=1, how="all")
    if returns.empty:
        return pd.DataFrame()
    return returns.corr()
