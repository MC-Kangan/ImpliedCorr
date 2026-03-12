"""Plotly charts for correlation analytics."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def implied_correlation_chart(history: pd.DataFrame, show_approx: bool, show_realized: bool) -> go.Figure:
    """Create the main implied correlation chart."""
    plot_data = history.sort_index()
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=plot_data.index,
            y=plot_data["rho_imp_full"],
            mode="lines",
            name="Implied Corr (Full)",
            line={"width": 2},
        )
    )
    if show_approx and "rho_imp_approx" in plot_data:
        figure.add_trace(
            go.Scatter(
                x=plot_data.index,
                y=plot_data["rho_imp_approx"],
                mode="lines",
                name="Implied Corr (Approx)",
                line={"dash": "dot"},
            )
        )
    if show_realized and "rho_realized" in plot_data:
        figure.add_trace(
            go.Scatter(
                x=plot_data.index,
                y=plot_data["rho_realized"],
                mode="lines",
                name="Realized Corr",
                line={"dash": "dash"},
            )
        )
    figure.update_layout(
        title="Historical Implied Correlation",
        yaxis_title="Correlation",
        hovermode="x unified",
        template="plotly_white",
        legend={"orientation": "h"},
    )
    figure.add_hline(y=0.0, line_dash="dot", line_color="gray")
    return figure


def spread_chart(history: pd.DataFrame) -> go.Figure:
    """Plot the implied minus realized correlation spread."""
    plot_data = history.sort_index()
    figure = go.Figure(
        go.Scatter(
            x=plot_data.index,
            y=plot_data["implied_minus_realized"],
            mode="lines",
            name="Implied - Realized",
            line={"width": 2},
        )
    )
    figure.update_layout(
        title="Implied Minus Realized Correlation",
        yaxis_title="Correlation Spread",
        hovermode="x unified",
        template="plotly_white",
    )
    figure.add_hline(y=0.0, line_dash="dot", line_color="gray")
    return figure


def realized_heatmap(corr_matrix: pd.DataFrame) -> go.Figure:
    """Create a heatmap for the latest realized correlation matrix."""
    figure = go.Figure(
        go.Heatmap(
            z=corr_matrix.to_numpy(),
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
        )
    )
    figure.update_layout(title="Latest Realized Correlation Matrix", template="plotly_white")
    return figure

