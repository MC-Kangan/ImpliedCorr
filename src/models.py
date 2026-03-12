"""Shared data models used across the application."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pandas as pd


ReturnType = Literal["log", "simple"]
DisplayMethod = Literal["full", "approx"]


@dataclass(frozen=True)
class BasketDefinition:
    """Parsed basket input from the uploaded CSV."""

    basket_ticker: str
    constituents: pd.DataFrame
    raw_upload: pd.DataFrame
    weight_input_sum: float
    normalized: bool

    @property
    def weights(self) -> pd.Series:
        """Return normalized constituent weights indexed by ticker."""
        frame = self.constituents.set_index("ticker")
        return frame["weight_normalized"].sort_index()


@dataclass(frozen=True)
class AppControls:
    """User-selected analytics controls."""

    start_date: date
    end_date: date
    realized_window: int
    return_type: ReturnType
    display_method: DisplayMethod
    normalize_weights_if_one: bool
    drop_missing_dates: bool


@dataclass
class LoadDiagnostics:
    """Track data quality diagnostics during load and alignment."""

    missing_vol_counts: dict[str, int] = field(default_factory=dict)
    missing_price_counts: dict[str, int] = field(default_factory=dict)
    missing_vol_tickers: list[str] = field(default_factory=list)
    missing_price_tickers: list[str] = field(default_factory=list)
    excluded_tickers: list[str] = field(default_factory=list)
    exclusion_reasons: dict[str, str] = field(default_factory=dict)
    vol_date_coverage: pd.DataFrame = field(default_factory=pd.DataFrame)
    price_date_coverage: pd.DataFrame = field(default_factory=pd.DataFrame)
    dropped_vol_dates: int = 0
    dropped_price_dates: int = 0


@dataclass(frozen=True)
class LoadedMarketData:
    """Aligned market data used by analytics."""

    basket_definition: BasketDefinition
    basket_vol: pd.Series
    constituent_vols: pd.DataFrame
    basket_prices: pd.Series
    constituent_prices: pd.DataFrame
    diagnostics: LoadDiagnostics


@dataclass(frozen=True)
class AnalyticsResult:
    """Computed analytics and display tables."""

    historical: pd.DataFrame
    contributions: pd.DataFrame
    latest_snapshot: pd.Series
    realized_correlation_matrix: pd.DataFrame
    constituent_snapshot: pd.DataFrame
    diagnostics: LoadDiagnostics
