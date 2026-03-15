"""Generate deterministic mock data for the Streamlit app."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VOL_DIR = ROOT / "data" / "vols"
PRICE_DIR = ROOT / "data" / "prices"
RVOL_DIR = ROOT / "data" / "rvols"

BASKET = "SX7P Index"
CONSTITUENTS = [
    ("SAN SQ Equity", 18.0),
    ("BNP FP Equity", 17.0),
    ("ACA FP Equity", 15.0),
    ("DBK GY Equity", 14.0),
    ("UCG IM Equity", 19.0),
    ("BBVA SM Equity", 17.0),
]


def ensure_dirs() -> None:
    VOL_DIR.mkdir(parents=True, exist_ok=True)
    PRICE_DIR.mkdir(parents=True, exist_ok=True)
    RVOL_DIR.mkdir(parents=True, exist_ok=True)


def generate() -> None:
    ensure_dirs()
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2025-01-02", "2025-12-31")
    n = len(dates)
    weights = np.array([weight / 100.0 for _, weight in CONSTITUENTS])

    common_factor = rng.normal(0.0002, 0.008, n)
    sector_factor = rng.normal(0.0001, 0.006, n)

    member_returns: dict[str, np.ndarray] = {}
    member_prices: dict[str, np.ndarray] = {}
    member_vols: dict[str, np.ndarray] = {}
    start_prices = np.array([74.0, 63.0, 15.0, 18.0, 42.0, 11.0])
    base_vols = np.array([0.29, 0.27, 0.25, 0.31, 0.33, 0.24])

    for idx, (ticker, _) in enumerate(CONSTITUENTS):
        idio = rng.normal(0.0, 0.012 + idx * 0.0008, n)
        ret = 0.58 * common_factor + 0.18 * sector_factor + idio
        member_returns[ticker] = ret
        prices = start_prices[idx] * np.exp(np.cumsum(ret))
        member_prices[ticker] = prices

        vol_noise = rng.normal(0.0, 0.004, n)
        vol = base_vols[idx] + 0.45 * np.abs(common_factor) + 0.15 * np.abs(idio) + vol_noise
        member_vols[ticker] = np.clip(vol, 0.12, 0.75)

    basket_returns = sum(weights[i] * member_returns[ticker] for i, (ticker, _) in enumerate(CONSTITUENTS))
    basket_prices = 100.0 * np.exp(np.cumsum(basket_returns))
    member_return_frame = pd.DataFrame(member_returns, index=dates)
    basket_return_series = pd.Series(basket_returns, index=dates, name=BASKET)

    member_vol_frame = pd.DataFrame(member_vols, index=dates)
    weighted_sq_term = (member_vol_frame.pow(2) * np.square(weights)).sum(axis=1)
    weighted_sum_sq = (member_vol_frame * weights).sum(axis=1).pow(2)
    cross_term = weighted_sum_sq - weighted_sq_term
    rho_series = 0.42 + 0.18 * np.sin(np.linspace(0, 3 * np.pi, n)) + rng.normal(0.0, 0.03, n)
    rho_series = np.clip(rho_series, 0.12, 0.86)
    basket_vol = np.sqrt(np.clip(weighted_sq_term + rho_series * cross_term, 1e-8, None))

    missing_dates = dates[::37]
    member_vol_frame.loc[missing_dates[:3], "DBK GY Equity"] = np.nan
    member_vol_frame.loc[missing_dates[3:6], "BBVA SM Equity"] = np.nan

    for ticker, _ in CONSTITUENTS:
        vol_frame = pd.DataFrame(
            {
                "date": dates,
                "ticker": ticker,
                "delta": 50,
                "tenor": "1Y",
                "implied_vol": member_vol_frame[ticker].round(6),
            }
        )
        px_frame = pd.DataFrame({"date": dates, "ticker": ticker, "close": np.round(member_prices[ticker], 6)})
        vol_frame.to_csv(VOL_DIR / f"{ticker}_vol_50d_1y.csv", index=False)
        px_frame.to_csv(PRICE_DIR / f"{ticker}_px.csv", index=False)

    basket_vol_frame = pd.DataFrame(
        {
            "date": dates,
            "ticker": BASKET,
            "delta": 50,
            "tenor": "1Y",
            "implied_vol": np.round(basket_vol, 6),
        }
    )
    basket_px_frame = pd.DataFrame({"date": dates, "ticker": BASKET, "close": np.round(basket_prices, 6)})
    basket_vol_frame.to_csv(VOL_DIR / f"{BASKET}_vol_50d_1y.csv", index=False)
    basket_px_frame.to_csv(PRICE_DIR / f"{BASKET}_px.csv", index=False)

    for window in [20, 60, 120]:
        member_rvol_frame = member_return_frame.rolling(window).std() * np.sqrt(252.0)
        basket_rvol_series = basket_return_series.rolling(window).std() * np.sqrt(252.0)

        for ticker, _ in CONSTITUENTS:
            rvol_frame = pd.DataFrame(
                {
                    "date": dates,
                    "ticker": ticker,
                    "window": window,
                    "realized_vol": member_rvol_frame[ticker].round(6),
                }
            )
            rvol_frame.to_csv(RVOL_DIR / f"{ticker}_rvol_{window}d.csv", index=False)

        basket_rvol_frame = pd.DataFrame(
            {
                "date": dates,
                "ticker": BASKET,
                "window": window,
                "realized_vol": basket_rvol_series.round(6),
            }
        )
        basket_rvol_frame.to_csv(RVOL_DIR / f"{BASKET}_rvol_{window}d.csv", index=False)


if __name__ == "__main__":
    generate()
