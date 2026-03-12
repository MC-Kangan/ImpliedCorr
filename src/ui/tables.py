"""Dataframe styling and table helpers."""

from __future__ import annotations

import pandas as pd


def prepare_export_table(history: pd.DataFrame) -> pd.DataFrame:
    """Flatten the historical analytics table for download/export."""
    export = history.reset_index().copy()
    export["date"] = export["date"].dt.strftime("%Y-%m-%d")
    return export

