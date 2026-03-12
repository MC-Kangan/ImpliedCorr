"""Streamlit application for implied correlation analytics."""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd
import streamlit as st

from src.charts.contribution_charts import contribution_bar_chart, constituent_scatter_chart
from src.charts.correlation_charts import implied_correlation_chart, realized_heatmap, spread_chart
from src.charts.vol_charts import volatility_comparison_chart
from src.config import PRICE_DIR, SAMPLE_DIR, VOL_DIR
from src.data_provider import MockCsvDataProvider
from src.loaders import build_analytics
from src.ui.messages import build_interpretation
from src.ui.sidebar import render_sidebar
from src.ui.tables import prepare_export_table
from src.utils.formatting import format_number, format_pct
from src.validators import BasketValidationError, parse_basket_csv

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Implied Correlation Monitor", layout="wide")


@st.cache_resource
def get_provider() -> MockCsvDataProvider:
    """Build a cached mock data provider instance."""
    return MockCsvDataProvider(vol_dir=VOL_DIR, price_dir=PRICE_DIR)


@st.cache_data
def load_default_basket_bytes() -> bytes:
    """Load the bundled sample basket upload."""
    return (SAMPLE_DIR / "sx7p_members.csv").read_bytes()


@st.cache_data
def compute_payload(
    basket_bytes: bytes,
    normalize_weights_if_one: bool,
    start_date: date,
    end_date: date,
    realized_window: int,
    return_type: str,
    drop_missing_dates: bool,
):
    """Cacheable wrapper for parsing and analytics."""
    validation = parse_basket_csv(basket_bytes, normalize_weights_if_one=normalize_weights_if_one)
    analytics = build_analytics(
        provider=get_provider(),
        basket=validation.basket,
        start_date=start_date,
        end_date=end_date,
        drop_missing_dates=drop_missing_dates,
        realized_window=realized_window,
        return_type=return_type,
    )
    return validation, analytics


def render_metric_row(snapshot: pd.Series) -> None:
    """Render top-line KPI cards."""
    cols = st.columns(5)
    cols[0].metric("Basket", snapshot["basket_ticker"])
    cols[1].metric("Constituents Used", str(int(snapshot["valid_constituent_count"])))
    cols[2].metric("Basket IV", format_pct(snapshot.get("basket_implied_vol")))
    cols[3].metric("Weighted Constituent IV", format_pct(snapshot.get("weighted_constituent_vol")))
    cols[4].metric("Implied Corr", format_pct(snapshot.get("rho_imp_full")))

    cols = st.columns(5)
    cols[0].metric("Approx Implied Corr", format_pct(snapshot.get("rho_imp_approx")))
    cols[1].metric("Realized Corr", format_pct(snapshot.get("latest_realized_corr")))
    cols[2].metric("Implied - Realized", format_pct(snapshot.get("implied_minus_realized")))
    percentile = snapshot.get("implied_corr_percentile")
    cols[3].metric("Percentile", "N/A" if pd.isna(percentile) else f"{percentile * 100:.0f}%")
    cols[4].metric("Weighted Constituent Variance", format_pct(snapshot.get("weighted_constituent_variance")))


def render_waiting_state() -> None:
    """Show instructions before the user runs the analysis."""
    st.info("Upload a basket CSV in the sidebar and click `Run analysis` to compute metrics and charts.")
    st.download_button(
        "Download sample basket CSV",
        data=load_default_basket_bytes(),
        file_name="sx7p_members.csv",
        mime="text/csv",
    )
    st.markdown(
        """
        Expected upload format:
        - First row: basket or index ticker
        - Remaining rows: constituent tickers and weights
        - Required columns: `ticker`, `weight`
        """
    )


def main() -> None:
    """Main Streamlit app."""
    st.title("Equity Basket Implied Correlation Monitor")
    st.caption(
        "Upload an index or basket definition to compare basket implied volatility, constituent implied volatility, and rolling realized correlation."
    )

    provider = get_provider()
    sample_basket = parse_basket_csv(load_default_basket_bytes()).basket
    sample_basket_vol = provider.get_vol(sample_basket.basket_ticker, 50, "1Y", date(2025, 1, 2), date(2025, 12, 31))
    min_date = sample_basket_vol["date"].min().date()
    max_date = sample_basket_vol["date"].max().date()

    controls, uploaded_file, run_analysis = render_sidebar(min_date=min_date, max_date=max_date)

    if run_analysis:
        if uploaded_file is None:
            st.sidebar.error("Please upload a basket CSV before running the analysis.")
        elif controls.start_date > controls.end_date:
            st.sidebar.error("Start date must be on or before end date.")
        else:
            st.session_state["analysis_request"] = {
                "basket_bytes": uploaded_file.getvalue(),
                "normalize_weights_if_one": controls.normalize_weights_if_one,
                "start_date": controls.start_date,
                "end_date": controls.end_date,
                "realized_window": controls.realized_window,
                "return_type": controls.return_type,
                "drop_missing_dates": controls.drop_missing_dates,
                "display_method": controls.display_method,
            }

    request = st.session_state.get("analysis_request")
    if request is None:
        render_waiting_state()
        st.stop()

    try:
        validation, analytics = compute_payload(
            basket_bytes=request["basket_bytes"],
            normalize_weights_if_one=request["normalize_weights_if_one"],
            start_date=request["start_date"],
            end_date=request["end_date"],
            realized_window=request["realized_window"],
            return_type=request["return_type"],
            drop_missing_dates=request["drop_missing_dates"],
        )
    except (BasketValidationError, ValueError, FileNotFoundError) as exc:
        st.error(str(exc))
        st.stop()

    for warning in validation.warnings:
        st.warning(warning)

    render_metric_row(analytics.latest_snapshot)

    tabs = st.tabs(
        ["Overview", "Historical Correlation", "Vol Diagnostics", "Constituents", "Data Quality", "Methodology"]
    )

    with tabs[0]:
        st.subheader("Snapshot")
        for message in build_interpretation(analytics.latest_snapshot, analytics.contributions):
            st.write(f"- {message}")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(
                contribution_bar_chart(analytics.contributions),
                use_container_width=True,
                key="overview_contribution_bar",
            )
        with col2:
            st.dataframe(validation.basket.constituents, use_container_width=True, hide_index=True)

    with tabs[1]:
        show_approx = request["display_method"] == "approx"
        st.plotly_chart(
            implied_correlation_chart(analytics.historical, show_approx=show_approx, show_realized=True),
            use_container_width=True,
            key="historical_implied_corr",
        )
        st.plotly_chart(spread_chart(analytics.historical), use_container_width=True, key="historical_spread")
        export_table = prepare_export_table(analytics.historical)
        st.dataframe(export_table, use_container_width=True, hide_index=True)
        st.download_button(
            "Download analytics CSV",
            export_table.to_csv(index=False).encode("utf-8"),
            file_name="implied_correlation_analytics.csv",
            mime="text/csv",
        )

    with tabs[2]:
        st.plotly_chart(
            volatility_comparison_chart(analytics.historical),
            use_container_width=True,
            key="vol_diagnostics_chart",
        )
        latest = analytics.latest_snapshot
        diagnostics_frame = pd.DataFrame(
            [
                ("Basket implied vol", format_pct(latest.get("basket_implied_vol"))),
                ("Weighted constituent vol", format_pct(latest.get("weighted_constituent_vol"))),
                ("Weighted constituent variance", format_pct(latest.get("weighted_constituent_variance"))),
                ("Implied correlation z-score", format_number(latest.get("implied_corr_zscore"))),
            ],
            columns=["Metric", "Value"],
        )
        st.dataframe(diagnostics_frame, use_container_width=True, hide_index=True)

    with tabs[3]:
        st.plotly_chart(
            contribution_bar_chart(analytics.contributions),
            use_container_width=True,
            key="constituents_contribution_bar",
        )
        st.plotly_chart(
            constituent_scatter_chart(analytics.constituent_snapshot),
            use_container_width=True,
            key="constituents_scatter",
        )
        st.dataframe(analytics.constituent_snapshot, use_container_width=True, hide_index=True)
        if not analytics.realized_correlation_matrix.empty:
            st.plotly_chart(
                realized_heatmap(analytics.realized_correlation_matrix),
                use_container_width=True,
                key="constituents_realized_heatmap",
            )

    with tabs[4]:
        st.write("Excluded tickers and reasons")
        reasons = []
        for ticker, reason in analytics.diagnostics.exclusion_reasons.items():
            reasons.append({"ticker": ticker, "reason": reason})
        if reasons:
            st.dataframe(pd.DataFrame(reasons), use_container_width=True, hide_index=True)
        else:
            st.info("No constituent tickers were excluded.")

        st.write("Volatility coverage")
        st.dataframe(analytics.diagnostics.vol_date_coverage, use_container_width=True, hide_index=True)
        st.write("Price coverage")
        st.dataframe(analytics.diagnostics.price_date_coverage, use_container_width=True, hide_index=True)
        dropped_frame = pd.DataFrame(
            [
                ("Dropped vol dates", analytics.diagnostics.dropped_vol_dates),
                ("Dropped price dates", analytics.diagnostics.dropped_price_dates),
            ],
            columns=["Metric", "Value"],
        )
        st.dataframe(dropped_frame, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.markdown("### Full constant-correlation formula")
        st.latex(
            r"\rho_{imp}(t)=\frac{\sigma_I(t)^2-\sum_i w_i^2 \sigma_i(t)^2}{\sum_{i \neq j} w_i w_j \sigma_i(t)\sigma_j(t)}"
        )

        st.markdown("### Approximation shown for comparison only")
        st.latex(r"\rho_{imp}^{approx}(t)\approx\frac{\sigma_I(t)^2}{\sum_i w_i \sigma_i(t)^2}")

        st.markdown("### Realized correlation proxy")
        st.markdown(
            r"""
            The app uses a rolling constituent covariance matrix, computes basket realized variance as
            $w^\top \Sigma_t w$, and backs out an average constant realized correlation with the same
            variance decomposition.
            """
        )

        st.markdown("### Important interpretation notes")
        st.markdown(
            """
            - Constant implied correlation compresses a full pairwise correlation surface into one scalar.
            - Implied correlation and realized correlation are diagnostics, not trade recommendations.
            - Dispersion PnL depends on weighting, smile, vega/theta profile, and implementation details, so it is not identical to a pure correlation swap payoff.
            """
        )


if __name__ == "__main__":
    main()
