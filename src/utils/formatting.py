"""Formatting helpers for Streamlit display."""

from __future__ import annotations

import math

import pandas as pd


def format_pct(value: float | None, decimals: int = 1) -> str:
    """Format decimal values as percentages."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_number(value: float | None, decimals: int = 2) -> str:
    """Format numbers with fixed decimal places."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"

