"""Date helper functions."""

from __future__ import annotations

from datetime import date, timedelta


def default_start_date(end_date: date) -> date:
    """Return an approximate one-year lookback from the end date."""
    return end_date - timedelta(days=365)

