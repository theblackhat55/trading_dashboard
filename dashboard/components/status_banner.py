from __future__ import annotations

import streamlit as st

from dashboard.loaders.spx_loader import latest_forecast_status


def render(spx_root) -> None:
    status = latest_forecast_status(spx_root)
    label = status.get("status", "Unknown")
    hybrid_date = status.get("hybrid_date") or "—"
    rs_date = status.get("range_skew_date") or "—"

    color = {
        "Compared": "#16a34a",
        "Awaiting Actuals": "#ea580c",
        "Missing Files": "#dc2626",
        "Partial Forecast Set": "#ca8a04",
        "Forecast Date Mismatch": "#dc2626",
    }.get(label, "#2563eb")

    st.markdown(
        f"""
        <div style="
            padding:0.75rem 1rem;
            border-radius:12px;
            background:{color};
            color:white;
            font-weight:600;
            margin-bottom:1rem;">
            SPX Status: {label} &nbsp;|&nbsp; Hybrid Date: {hybrid_date} &nbsp;|&nbsp; Range+Skew Date: {rs_date}
        </div>
        """,
        unsafe_allow_html=True,
    )
