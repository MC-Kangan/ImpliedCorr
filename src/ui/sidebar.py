"""Sidebar rendering helpers."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.models import AppControls
from src.utils.dates import default_start_date


def render_sidebar(min_date: date, max_date: date) -> tuple[AppControls, object, bool]:
    """Render sidebar controls and return the selected app state."""
    st.sidebar.header("Inputs")
    with st.sidebar.form("analysis_inputs"):
        uploaded_file = st.file_uploader("Basket CSV", type=["csv"])
        start_date = st.date_input(
            "Start date",
            value=max(min_date, default_start_date(max_date)),
            min_value=min_date,
            max_value=max_date,
        )
        end_date = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)
        realized_window = st.selectbox("Rolling realized window", options=[20, 60, 120], index=1)
        display_method = st.selectbox("Display comparison", options=["full", "approx"], index=0)
        normalize_weights_if_one = st.checkbox("Normalize weights if file sums to 1", value=True)
        drop_missing_dates = st.checkbox("Drop missing dates conservatively", value=True)
        run_analysis = st.form_submit_button("Run analysis", use_container_width=True)

    controls = AppControls(
        start_date=start_date,
        end_date=end_date,
        realized_window=realized_window,
        display_method=display_method,
        normalize_weights_if_one=normalize_weights_if_one,
        drop_missing_dates=drop_missing_dates,
    )
    return controls, uploaded_file, run_analysis
