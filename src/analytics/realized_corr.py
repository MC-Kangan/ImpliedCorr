"""Realized correlation calculations from historical prices."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import EPSILON
from src.models import ReturnType


def compute_returns(prices: pd.DataFrame, return_type: ReturnType) -> pd.DataFrame:
    """Compute aligned constituent returns."""
    prices = prices.sort_index()
    if return_type == "log":
        returns = np.log(prices / prices.shift(1))
    else:
        returns = prices.pct_change()
    return returns.dropna(how="all")


def compute_realized_correlation_history(
    constituent_prices: pd.DataFrame,
    weights: pd.Series,
    window: int,
    return_type: ReturnType,
    epsilon: float = EPSILON,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute rolling realized correlation and the latest correlation matrix."""
    returns = compute_returns(constituent_prices, return_type=return_type)
    common_weights = weights.reindex(constituent_prices.columns)
    if common_weights.isna().any():
        missing = ", ".join(common_weights[common_weights.isna()].index.tolist())
        raise ValueError(f"Weights missing for tickers: {missing}")

    rows: list[dict[str, float | pd.Timestamp]] = []
    latest_corr = pd.DataFrame(index=constituent_prices.columns, columns=constituent_prices.columns, dtype=float)
    w = common_weights.to_numpy(dtype=float)

    for end_idx in range(window - 1, len(returns)):
        window_returns = returns.iloc[end_idx - window + 1 : end_idx + 1].dropna(how="any")
        if window_returns.shape[0] < max(2, window // 2):
            continue

        cov = window_returns.cov()
        vols = pd.Series(np.sqrt(np.diag(cov.to_numpy())), index=cov.index)
        basket_variance = float(w @ cov.to_numpy() @ w)
        single_name_term = float((np.square(w) * np.square(vols.to_numpy())).sum())
        cross_term = float(np.square((w * vols.to_numpy()).sum()) - single_name_term)
        rho_realized = np.nan if abs(cross_term) <= epsilon else (basket_variance - single_name_term) / cross_term

        rows.append(
            {
                "date": returns.index[end_idx],
                "rho_realized": rho_realized,
                "realized_basket_variance": basket_variance,
                "realized_single_name_variance_term": single_name_term,
                "realized_cross_term": cross_term,
            }
        )
        latest_corr = window_returns.corr()

    history = pd.DataFrame(rows)
    if history.empty:
        return history, latest_corr
    history["date"] = pd.to_datetime(history["date"])
    history = history.set_index("date").sort_index()
    history.index.name = "date"
    return history, latest_corr

