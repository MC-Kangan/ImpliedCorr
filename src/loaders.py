"""High-level loader that ties market data and analytics together."""

from __future__ import annotations

import pandas as pd

from src.analytics.correlation import compute_log_return_correlation_matrix
from src.analytics.dispersion_metrics import add_dispersion_metrics
from src.analytics.alignment import load_market_data
from src.analytics.contributions import compute_latest_contributions
from src.analytics.implied_corr import compute_implied_correlation_history, current_percentile
from src.analytics.realized_corr import compute_realized_correlation_history
from src.models import AnalyticsResult, BasketDefinition
from src.utils.stats import z_score


def build_analytics(
    provider,
    basket: BasketDefinition,
    start_date,
    end_date,
    drop_missing_dates: bool,
    realized_window: int,
) -> AnalyticsResult:
    """Load data and compute the full analytics payload."""
    market_data = load_market_data(
        provider=provider,
        basket=basket,
        start_date=start_date,
        end_date=end_date,
        drop_missing_dates=drop_missing_dates,
        realized_window=realized_window,
    )

    weights = market_data.basket_definition.weights
    implied_history = compute_implied_correlation_history(
        basket_vol=market_data.basket_vol,
        constituent_vols=market_data.constituent_vols,
        weights=weights,
    )
    realized_history = compute_realized_correlation_history(
        basket_rvol=market_data.basket_rvol,
        constituent_rvols=market_data.constituent_rvols,
        weights=weights,
    )

    history = implied_history.join(realized_history, how="left")
    history = add_dispersion_metrics(history)
    history["implied_minus_realized"] = history["corr_spread"]
    history["implied_corr_percentile"] = current_percentile(history["rho_imp_full"])
    history["implied_corr_zscore"] = z_score(history["rho_imp_full"])

    contributions = compute_latest_contributions(
        constituent_vols=market_data.constituent_vols,
        weights=weights,
    )
    constituent_snapshot = contributions.copy()
    latest_snapshot = history.iloc[-1].copy()
    latest_snapshot["basket_ticker"] = market_data.basket_definition.basket_ticker
    latest_snapshot["valid_constituent_count"] = int(market_data.constituent_vols.shape[1])
    latest_snapshot["implied_corr_percentile"] = current_percentile(history["rho_imp_full"])
    latest_snapshot["latest_realized_corr"] = latest_snapshot.get("rho_realized")
    latest_snapshot["latest_date"] = history.index.max()
    corr_matrix = compute_log_return_correlation_matrix(market_data.constituent_prices, forward_fill=not drop_missing_dates)

    return AnalyticsResult(
        historical=history,
        contributions=contributions,
        latest_snapshot=latest_snapshot,
        realized_correlation_matrix=corr_matrix,
        constituent_snapshot=constituent_snapshot,
        diagnostics=market_data.diagnostics,
    )
