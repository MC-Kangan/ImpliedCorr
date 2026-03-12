"""Validation and parsing for uploaded basket definition files."""

from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd

from src.config import WEIGHT_TOLERANCE_PCT
from src.models import BasketDefinition


class BasketValidationError(ValueError):
    """Raised when the basket upload fails validation."""


@dataclass(frozen=True)
class BasketValidationResult:
    """Return value for validation to keep UI logic simple."""

    basket: BasketDefinition
    warnings: list[str]


def parse_basket_csv(file_bytes: bytes, normalize_weights_if_one: bool = True) -> BasketValidationResult:
    """Parse and validate the uploaded basket CSV."""
    try:
        upload = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:  # pragma: no cover - pandas raises multiple concrete exceptions
        raise BasketValidationError(f"Unable to read uploaded CSV: {exc}") from exc

    required_columns = {"ticker", "weight"}
    missing_columns = required_columns.difference(upload.columns.str.lower())
    if missing_columns:
        raise BasketValidationError("Upload must contain 'ticker' and 'weight' columns.")

    upload.columns = [column.lower() for column in upload.columns]
    if len(upload) < 3:
        raise BasketValidationError("Upload must contain at least one basket row and two constituent rows.")

    frame = upload.loc[:, ["ticker", "weight"]].copy()
    frame["ticker"] = frame["ticker"].astype(str).str.strip()
    frame["weight"] = pd.to_numeric(frame["weight"], errors="coerce")

    if frame["ticker"].eq("").any():
        raise BasketValidationError("Ticker values cannot be blank.")
    if frame["weight"].isna().any():
        raise BasketValidationError("All weights must be numeric.")
    if frame["ticker"].duplicated().any():
        dupes = ", ".join(sorted(frame.loc[frame["ticker"].duplicated(), "ticker"].unique()))
        raise BasketValidationError(f"Duplicate tickers found in upload: {dupes}")

    basket_ticker = frame.iloc[0]["ticker"]
    constituents = frame.iloc[1:].copy().reset_index(drop=True)
    if basket_ticker in set(constituents["ticker"]):
        raise BasketValidationError("Basket ticker must not appear again among constituents.")

    raw_weight_sum = float(constituents["weight"].sum())
    normalized = False
    warnings: list[str] = []

    if normalize_weights_if_one and abs(raw_weight_sum - 1.0) <= 0.01:
        constituents["weight_pct"] = constituents["weight"] * 100.0
        normalized = True
        warnings.append("Constituent weights summed near 1.0 and were scaled to percentage terms.")
    else:
        constituents["weight_pct"] = constituents["weight"]

    weight_sum_pct = float(constituents["weight_pct"].sum())
    if abs(weight_sum_pct - 100.0) > WEIGHT_TOLERANCE_PCT:
        raise BasketValidationError(
            f"Constituent weights must sum to 100 +/- {WEIGHT_TOLERANCE_PCT:.1f}. Current sum is {weight_sum_pct:.2f}."
        )

    constituents["weight_normalized"] = constituents["weight_pct"] / weight_sum_pct
    constituents = constituents.sort_values("weight_normalized", ascending=False).reset_index(drop=True)

    basket = BasketDefinition(
        basket_ticker=basket_ticker,
        constituents=constituents,
        raw_upload=frame,
        weight_input_sum=raw_weight_sum,
        normalized=normalized,
    )
    return BasketValidationResult(basket=basket, warnings=warnings)

