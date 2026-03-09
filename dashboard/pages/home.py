from __future__ import annotations

import streamlit as st

from dashboard.config import OPTIONS_ALGO_ROOT, SPX_ALGO_ROOT
from dashboard.loaders import options_loader, spx_loader


def _status_chip(label: str, ok: bool) -> None:
    color = "#16a34a" if ok else "#dc2626"
    text = "OK" if ok else "Missing"
    st.markdown(
        f"""
        <div style="
            display:inline-block;
            padding:0.30rem 0.65rem;
            border-radius:999px;
            background:{color};
            color:white;
            font-weight:600;
            font-size:0.85rem;">
            {label}: {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render():
    st.title("📊 Shared Trading Dashboard")
    st.caption("Unified UI for SPX Algo and Options Algo")

    st.subheader("System Status")

    left, right = st.columns(2)

    with left:
        st.markdown("## SPX Algo")

        latest_signal = spx_loader.load_latest_signal(SPX_ALGO_ROOT)
        hybrid = spx_loader.load_latest_hybrid_forecast(SPX_ALGO_ROOT)
        range_skew = spx_loader.load_latest_range_skew_forecast(SPX_ALGO_ROOT)
        scorecard = spx_loader.load_daily_comparison_scorecard(SPX_ALGO_ROOT)
        freshness = spx_loader.file_freshness(SPX_ALGO_ROOT)

        sig_ok = latest_signal is not None
        hy_ok = hybrid is not None
        rs_ok = range_skew is not None
        sc_ok = not scorecard.empty

        c1, c2 = st.columns(2)
        with c1:
            _status_chip("Latest Signal", sig_ok)
        with c2:
            _status_chip("Comparison Scorecard", sc_ok)

        c3, c4 = st.columns(2)
        with c3:
            _status_chip("Hybrid Forecast", hy_ok)
        with c4:
            _status_chip("Range+Skew Forecast", rs_ok)

        st.markdown("### Forecast Summary")
        status = spx_loader.latest_forecast_status(SPX_ALGO_ROOT)

        m1, m2, m3 = st.columns(3)
        m1.metric("Forecast Status", status.get("status", "—"))
        m2.metric("Forecast Date", status.get("hybrid_date") or status.get("range_skew_date") or "—")
        m3.metric("Scorecard Rows", len(scorecard) if not scorecard.empty else 0)

        if freshness.empty:
            st.info("No SPX freshness data available.")
        else:
            display_cols = [c for c in ["name", "exists", "modified_at", "age_hours"] if c in freshness.columns]
            st.markdown("### SPX File Freshness")
            st.dataframe(freshness[display_cols], use_container_width=True, height=260)

    with right:
        st.markdown("## Options Algo")

        latest_options_signal = options_loader.load_latest_signal()
        positions = options_loader.load_positions()
        outcomes = options_loader.load_trade_outcomes()

        sig_ok = latest_options_signal is not None
        pos_ok = positions is not None
        out_ok = outcomes is not None and not outcomes.empty

        c1, c2 = st.columns(2)
        with c1:
            _status_chip("Latest Options Signal", sig_ok)
        with c2:
            _status_chip("Trade Outcomes", out_ok)

        c3, c4 = st.columns(2)
        with c3:
            _status_chip("Positions", pos_ok)
        with c4:
            _status_chip("Options Root", OPTIONS_ALGO_ROOT.exists())

        st.markdown("### Options Summary")

        generated_at = "—"
        scan_date = "—"
        if isinstance(latest_options_signal, dict):
            generated_at = latest_options_signal.get("generated_at", "—")
            scan_date = latest_options_signal.get("scan_date", "—")

        position_count = 0
        if isinstance(positions, dict):
            if "positions" in positions and isinstance(positions["positions"], list):
                position_count = len(positions["positions"])
            else:
                position_count = len(positions)

        o1, o2, o3 = st.columns(3)
        o1.metric("Scan Date", scan_date)
        o2.metric("Generated At", generated_at)
        o3.metric("Positions", position_count)

        if outcomes is not None and not outcomes.empty:
            st.markdown("### Recent Trade Outcomes")
            st.dataframe(outcomes.tail(10), use_container_width=True, height=260)
        else:
            st.info("No trade outcomes found for Options Algo.")

    st.divider()
    st.subheader("Quick Navigation")
    st.markdown(
        """
        - **SPX Daily Monitor** → latest predicted vs actual view
        - **SPX Forecasts** → latest forecast payload details
        - **SPX Comparison History** → scorecard and model tracking
        - **SPX Archive Browser** → archived forecast inspection
        - **Ops / Freshness** → file freshness / missing artifact checks
        """
    )
