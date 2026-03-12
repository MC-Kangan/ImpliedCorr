"""Interpretation layer for neutral analytics commentary."""

from __future__ import annotations

import pandas as pd

from src.utils.formatting import format_pct


def build_interpretation(snapshot: pd.Series, contributions: pd.DataFrame) -> list[str]:
    """Generate neutral, descriptive interpretation messages."""
    messages: list[str] = []

    percentile = snapshot.get("implied_corr_percentile")
    if pd.notna(snapshot.get("rho_imp_full")):
        percentile_text = "N/A" if pd.isna(percentile) else f"{percentile * 100:.0f}th percentile"
        messages.append(
            f"Current implied correlation is {format_pct(snapshot.get('rho_imp_full'))}, sitting in the {percentile_text} of the selected lookback."
        )

    if pd.notna(snapshot.get("weighted_constituent_vol")) and pd.notna(snapshot.get("basket_implied_vol")):
        relation = "above" if snapshot["basket_implied_vol"] > snapshot["weighted_constituent_vol"] else "below"
        messages.append(
            f"Basket implied vol is {relation} the weighted constituent vol proxy ({format_pct(snapshot.get('basket_implied_vol'))} vs {format_pct(snapshot.get('weighted_constituent_vol'))})."
        )

    if pd.notna(snapshot.get("implied_minus_realized")):
        messages.append(
            f"Implied correlation is {format_pct(snapshot.get('implied_minus_realized'))} relative to realized correlation on the latest date."
        )

    if not contributions.empty:
        leaders = ", ".join(contributions.head(3)["ticker"].tolist())
        messages.append(f"The largest weighted-variance contributors are {leaders}.")

    messages.append(
        "Constant implied correlation is a simplification of the full pairwise correlation surface and should be treated as a diagnostic rather than a tradable payoff."
    )
    return messages

