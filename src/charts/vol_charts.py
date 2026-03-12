"""Plotly charts for volatility diagnostics."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def volatility_comparison_chart(history: pd.DataFrame) -> go.Figure:
    """Compare basket and constituent proxy implied volatilities."""
    plot_data = history.sort_index()
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=plot_data.index,
            y=plot_data["basket_implied_vol"],
            mode="lines",
            name="Basket Implied Vol",
            line={"width": 2},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=plot_data.index,
            y=plot_data["weighted_constituent_vol"],
            mode="lines",
            name="Weighted Constituent Vol",
            line={"dash": "dot"},
        )
    )
    figure.update_layout(
        title="Volatility Comparison",
        yaxis_title="Volatility (decimal)",
        hovermode="x unified",
        template="plotly_white",
        legend={"orientation": "h"},
    )
    return figure

