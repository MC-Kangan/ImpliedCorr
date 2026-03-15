"""Data provider abstractions and CSV-backed implementation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

import pandas as pd

logger = logging.getLogger(__name__)


class DataProvider(Protocol):
    """Abstract market data provider interface."""

    def get_vol(
        self,
        ticker: str,
        delta: int,
        tenor: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Return implied volatility history for a ticker."""

    def px(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Return price history for a ticker."""

    def get_rvol(self, ticker: str, window: int, start_date: date, end_date: date) -> pd.DataFrame:
        """Return realized volatility history for a ticker."""


@dataclass
class MockCsvDataProvider:
    """CSV-backed provider that mirrors the future production interface."""

    vol_dir: Path
    rvol_dir: Path
    price_dir: Path

    def _read_csv(self, path: Path, date_col: str = "date") -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path, parse_dates=[date_col])
        frame[date_col] = pd.to_datetime(frame[date_col]).dt.tz_localize(None)
        return frame.sort_values(date_col).reset_index(drop=True)

    @staticmethod
    def _filter_dates(frame: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        mask = frame["date"].between(start_ts, end_ts)
        return frame.loc[mask].copy()

    def get_vol(
        self,
        ticker: str,
        delta: int,
        tenor: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        filename = f"{ticker}_vol_{delta}d_{tenor.lower()}.csv"
        path = self.vol_dir / filename
        logger.debug("Loading vol data for %s from %s", ticker, path)
        frame = self._read_csv(path)
        expected = frame[(frame["ticker"] == ticker) & (frame["delta"] == delta) & (frame["tenor"] == tenor)]
        if expected.empty:
            raise ValueError(f"No matching vol records found for {ticker}, delta={delta}, tenor={tenor}")
        return self._filter_dates(expected, start_date, end_date)

    def px(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
        filename = f"{ticker}_px.csv"
        path = self.price_dir / filename
        logger.debug("Loading price data for %s from %s", ticker, path)
        frame = self._read_csv(path)
        expected = frame[frame["ticker"] == ticker]
        if expected.empty:
            raise ValueError(f"No matching price records found for {ticker}")
        return self._filter_dates(expected, start_date, end_date)

    def get_rvol(self, ticker: str, window: int, start_date: date, end_date: date) -> pd.DataFrame:
        filename = f"{ticker}_rvol_{window}d.csv"
        path = self.rvol_dir / filename
        logger.debug("Loading realized vol data for %s from %s", ticker, path)
        frame = self._read_csv(path)
        expected = frame[(frame["ticker"] == ticker) & (frame["window"] == window)]
        if expected.empty:
            raise ValueError(f"No matching realized vol records found for {ticker}, window={window}")
        return self._filter_dates(expected, start_date, end_date)


@dataclass
class CloudDataProvider:
    """Placeholder for the future production cloud/cache provider."""

    def get_vol(
        self,
        ticker: str,
        delta: int,
        tenor: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        raise NotImplementedError(
            "CloudDataProvider is a placeholder. Replace this stub with the production cache adapter."
        )

    def px(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
        raise NotImplementedError(
            "CloudDataProvider is a placeholder. Replace this stub with the production cache adapter."
        )

    def get_rvol(self, ticker: str, window: int, start_date: date, end_date: date) -> pd.DataFrame:
        raise NotImplementedError(
            "CloudDataProvider is a placeholder. Replace this stub with the production cache adapter."
        )
