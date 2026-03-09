from __future__ import annotations

import streamlit as st

from dashboard.config import APP_ICON, APP_TITLE, OPTIONS_ALGO_ROOT, SPX_ALGO_ROOT
from dashboard.pages import (
    home,
    ops_freshness,
    options_overview,
    spx_archive_browser,
    spx_comparison_history,
    spx_daily_monitor,
    spx_forecasts,
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("📊 Trading Dashboard")
page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home",
        "📈 SPX Daily Monitor",
        "📉 SPX Forecasts",
        "📊 SPX Comparison History",
        "🗂️ SPX Archive Browser",
        "🧾 Options Overview",
        "🛠️ Ops / Freshness",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Shared dashboard for SPX Algo + Options Algo")

if page == "🏠 Home":
    home.render()
elif page == "📈 SPX Daily Monitor":
    spx_daily_monitor.render(SPX_ALGO_ROOT)
elif page == "📉 SPX Forecasts":
    spx_forecasts.render()
elif page == "📊 SPX Comparison History":
    spx_comparison_history.render(SPX_ALGO_ROOT)
elif page == "🗂️ SPX Archive Browser":
    spx_archive_browser.render(SPX_ALGO_ROOT)
elif page == "🧾 Options Overview":
    options_overview.render()
elif page == "🛠️ Ops / Freshness":
    ops_freshness.render(SPX_ALGO_ROOT)
