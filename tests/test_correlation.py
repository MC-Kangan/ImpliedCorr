from __future__ import annotations

import numpy as np
import pandas as pd

try:
    import pytest
except ModuleNotFoundError:  # pragma: no cover - import guard for environments without pytest installed
    class _PytestApprox:
        @staticmethod
        def approx(value: float):
            return value

    pytest = _PytestApprox()

from src.analytics.implied_corr import compute_implied_correlation_history
from src.analytics.realized_corr import compute_realized_correlation_history


def test_two_asset_portfolio_recovers_half_correlation() -> None:
    dates = pd.date_range("2025-01-01", periods=1, freq="B")
    weights = pd.Series({"A": 0.5, "B": 0.5})
    vols = pd.DataFrame({"A": [0.20], "B": [0.20]}, index=dates)
    basket_vol = pd.Series([np.sqrt(0.5**2 * 0.2**2 + 0.5**2 * 0.2**2 + 2 * (0.5 * 0.5 * 0.2 * 0.2 * 0.5))], index=dates)

    implied = compute_implied_correlation_history(basket_vol=basket_vol, constituent_vols=vols, weights=weights)
    realized = compute_realized_correlation_history(basket_rvol=basket_vol, constituent_rvols=vols, weights=weights)

    assert implied.iloc[0]["rho_imp_full"] == pytest.approx(0.5)
    assert realized.iloc[0]["rho_realized"] == pytest.approx(0.5)


def test_random_multi_asset_basket_recovers_true_correlation() -> None:
    rng = np.random.default_rng(12)
    dates = pd.date_range("2025-01-01", periods=1, freq="B")
    tickers = ["A", "B", "C", "D", "E"]
    weights = pd.Series(rng.dirichlet(np.ones(len(tickers))), index=tickers)
    vols = pd.DataFrame([rng.uniform(0.15, 0.35, size=len(tickers))], index=dates, columns=tickers)
    true_corr = 0.3

    diag_term = ((weights**2) * vols.iloc[0].pow(2)).sum()
    cross_term = (weights.mul(vols.iloc[0]).sum() ** 2) - diag_term
    basket_vol = pd.Series([np.sqrt(diag_term + true_corr * cross_term)], index=dates)

    implied = compute_implied_correlation_history(basket_vol=basket_vol, constituent_vols=vols, weights=weights)
    realized = compute_realized_correlation_history(basket_rvol=basket_vol, constituent_rvols=vols, weights=weights)

    assert implied.iloc[0]["rho_imp_full"] == pytest.approx(true_corr)
    assert realized.iloc[0]["rho_realized"] == pytest.approx(true_corr)


def test_vectorized_historical_series_has_expected_shape_and_bounds() -> None:
    dates = pd.date_range("2025-01-01", periods=5, freq="B")
    weights = pd.Series({"A": 0.4, "B": 0.35, "C": 0.25})
    vols = pd.DataFrame(
        {
            "A": [0.20, 0.21, 0.22, 0.23, 0.24],
            "B": [0.18, 0.19, 0.20, 0.21, 0.22],
            "C": [0.25, 0.24, 0.23, 0.22, 0.21],
        },
        index=dates,
    )
    true_corr = 0.4
    weighted = vols.mul(weights, axis=1)
    diag_term = (vols.pow(2) * weights.pow(2)).sum(axis=1)
    cross_term = weighted.sum(axis=1).pow(2) - diag_term
    basket_vol = np.sqrt(diag_term + true_corr * cross_term)

    realized = compute_realized_correlation_history(basket_rvol=basket_vol, constituent_rvols=vols, weights=weights)

    assert realized.index.equals(dates)
    assert len(realized) == len(dates)
    assert realized["rho_realized"].between(-1.0, 1.0).all()
    assert realized["rho_realized"].iloc[-1] == pytest.approx(true_corr)
