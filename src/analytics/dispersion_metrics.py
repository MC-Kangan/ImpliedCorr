"""Derived dispersion metrics used by the dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import EPSILON


def add_dispersion_metrics(history: pd.DataFrame) -> pd.DataFrame:
    """Add JPM-style proxy and spread diagnostics to the analytics table."""
    enriched = history.copy()
    denom = enriched["weighted_constituent_vol"].where(enriched["weighted_constituent_vol"].abs() > EPSILON)
    enriched["rho_proxy"] = (enriched["basket_implied_vol"] / denom).pow(2)
    enriched["corr_spread"] = enriched["rho_imp_full"] - enriched["rho_realized"]
    enriched["index_minus_weighted_constituent_vol"] = (
        enriched["basket_implied_vol"] - enriched["weighted_constituent_vol"]
    )
    enriched["diag_term_pct_of_basket_var"] = np.where(
        enriched["basket_variance"].abs() > EPSILON,
        enriched["diag_term"] / enriched["basket_variance"],
        np.nan,
    )
    return enriched
