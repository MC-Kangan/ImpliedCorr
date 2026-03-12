"""Helpers for loading and aligning market data."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

import pandas as pd

from src.config import MIN_CONSTITUENTS
from src.data_provider import DataProvider
from src.models import BasketDefinition, LoadDiagnostics, LoadedMarketData


def _series_coverage(series_map: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for ticker, series in series_map.items():
        rows.append(
            {
                "ticker": ticker,
                "rows": int(series.shape[0]),
                "missing_values": int(series.isna().sum()),
                "first_valid_date": series.dropna().index.min(),
                "last_valid_date": series.dropna().index.max(),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["ticker", "rows", "missing_values", "first_valid_date", "last_valid_date"])
    return pd.DataFrame(rows).sort_values("ticker").reset_index(drop=True)


def _fetch_series(
    provider: DataProvider,
    tickers: list[str],
    loader_type: str,
    start_date: date,
    end_date: date,
) -> tuple[dict[str, pd.Series], list[str], dict[str, str]]:
    series_map: dict[str, pd.Series] = {}
    missing_tickers: list[str] = []
    reasons: dict[str, str] = {}

    for ticker in tickers:
        try:
            if loader_type == "vol":
                frame = provider.get_vol(ticker, delta=50, tenor="1Y", start_date=start_date, end_date=end_date)
                series = frame.set_index("date")["implied_vol"].sort_index()
            else:
                frame = provider.px(ticker, start_date=start_date, end_date=end_date)
                series = frame.set_index("date")["close"].sort_index()
        except (FileNotFoundError, ValueError) as exc:
            missing_tickers.append(ticker)
            reasons[ticker] = str(exc)
            continue

        if series.empty:
            missing_tickers.append(ticker)
            reasons[ticker] = f"No {loader_type} data found in requested date range."
            continue
        series_map[ticker] = series

    return series_map, missing_tickers, reasons


def _align_series_map(
    series_map: dict[str, pd.Series],
    drop_missing_dates: bool,
) -> tuple[pd.DataFrame, int]:
    if not series_map:
        return pd.DataFrame(), 0

    frame = pd.concat(series_map, axis=1).sort_index()
    before = len(frame)
    if drop_missing_dates:
        frame = frame.dropna(how="any")
    dropped = before - len(frame)
    frame.columns = frame.columns.droplevel(0) if isinstance(frame.columns, pd.MultiIndex) else frame.columns
    frame.index.name = "date"
    return frame, dropped


def load_market_data(
    provider: DataProvider,
    basket: BasketDefinition,
    start_date: date,
    end_date: date,
    drop_missing_dates: bool,
) -> LoadedMarketData:
    """Load and align market data for the basket ticker and its constituents."""
    diagnostics = LoadDiagnostics()
    member_tickers = basket.constituents["ticker"].tolist()

    vol_map, missing_vols, vol_reasons = _fetch_series(
        provider=provider,
        tickers=[basket.basket_ticker, *member_tickers],
        loader_type="vol",
        start_date=start_date,
        end_date=end_date,
    )
    px_map, missing_prices, price_reasons = _fetch_series(
        provider=provider,
        tickers=[basket.basket_ticker, *member_tickers],
        loader_type="price",
        start_date=start_date,
        end_date=end_date,
    )

    diagnostics.missing_vol_tickers = missing_vols
    diagnostics.missing_price_tickers = missing_prices
    diagnostics.exclusion_reasons.update(vol_reasons)
    diagnostics.exclusion_reasons.update(price_reasons)

    available_members = [
        ticker for ticker in member_tickers if ticker in vol_map and ticker in px_map
    ]
    excluded = sorted(set(member_tickers).difference(available_members))
    diagnostics.excluded_tickers = excluded
    for ticker in excluded:
        diagnostics.exclusion_reasons.setdefault(ticker, "Missing either vol or price history.")

    if basket.basket_ticker not in vol_map or basket.basket_ticker not in px_map:
        raise ValueError(f"Basket ticker {basket.basket_ticker} must have both vol and price data available.")
    if len(available_members) < MIN_CONSTITUENTS:
        raise ValueError("At least two constituents with both vol and price histories are required.")

    aligned_constituents = basket.constituents[basket.constituents["ticker"].isin(available_members)].copy()
    aligned_basket = BasketDefinition(
        basket_ticker=basket.basket_ticker,
        constituents=aligned_constituents.reset_index(drop=True),
        raw_upload=basket.raw_upload,
        weight_input_sum=basket.weight_input_sum,
        normalized=basket.normalized,
    )

    vol_series_map = {ticker: vol_map[ticker] for ticker in [basket.basket_ticker, *available_members]}
    price_series_map = {ticker: px_map[ticker] for ticker in [basket.basket_ticker, *available_members]}

    diagnostics.vol_date_coverage = _series_coverage(vol_series_map)
    diagnostics.price_date_coverage = _series_coverage(price_series_map)
    diagnostics.missing_vol_counts = {ticker: int(series.isna().sum()) for ticker, series in vol_series_map.items()}
    diagnostics.missing_price_counts = {ticker: int(series.isna().sum()) for ticker, series in price_series_map.items()}

    vol_frame, diagnostics.dropped_vol_dates = _align_series_map(vol_series_map, drop_missing_dates)
    price_frame, diagnostics.dropped_price_dates = _align_series_map(price_series_map, drop_missing_dates)

    common_dates = vol_frame.index.intersection(price_frame.index)
    if common_dates.empty:
        raise ValueError("No overlapping dates remain after aligning volatility and price histories.")

    vol_frame = vol_frame.loc[common_dates]
    price_frame = price_frame.loc[common_dates]
    if vol_frame.empty or price_frame.empty:
        raise ValueError("Aligned market data is empty after intersection.")

    return LoadedMarketData(
        basket_definition=aligned_basket,
        basket_vol=vol_frame[aligned_basket.basket_ticker],
        constituent_vols=vol_frame[available_members],
        basket_prices=price_frame[aligned_basket.basket_ticker],
        constituent_prices=price_frame[available_members],
        diagnostics=diagnostics,
    )

