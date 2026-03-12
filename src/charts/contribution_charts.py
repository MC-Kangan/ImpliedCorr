"""Plotly charts for constituent contribution diagnostics."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def contribution_bar_chart(contributions: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Create a horizontal bar chart of weighted variance contributions."""
    plot_data = contributions.head(top_n).sort_values("weighted_variance_contribution", ascending=True)
    figure = go.Figure(
        go.Bar(
            x=plot_data["weighted_variance_contribution"],
            y=plot_data["ticker"],
            orientation="h",
            text=plot_data["variance_contribution_pct"].map(lambda value: f"{value * 100:.1f}%"),
        )
    )
    figure.update_layout(
        title="Top Weighted Variance Contributors",
        xaxis_title="w^2 * sigma^2",
        yaxis_title="Ticker",
        template="plotly_white",
    )
    return figure


def constituent_scatter_chart(contributions: pd.DataFrame) -> go.Figure:
    """Scatter plot of weight versus implied vol sized by contribution."""
    figure = px.scatter(
        contributions,
        x="weight",
        y="implied_vol",
        size="weighted_variance_contribution",
        hover_name="ticker",
        title="Constituent Weight vs Implied Vol",
        template="plotly_white",
    )
    figure.update_layout(xaxis_title="Weight", yaxis_title="Implied Vol")
    return figure

