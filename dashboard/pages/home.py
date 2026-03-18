from __future__ import annotations

import streamlit as st

from dashboard.config import OPTIONS_ALGO_V2_DATA_ROOT, OPTIONS_ALGO_ROOT, SPX_ALGO_ROOT
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


def _state_chip(label: str, active: bool, true_text: str = "Yes", false_text: str = "No") -> None:
    color = "#ea580c" if active else "#16a34a"
    text = true_text if active else false_text
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
    st.caption("Unified UI for SPX Algo and Options Algo V2")

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
        m2.metric(
            "Forecast Date",
            status.get("hybrid_date") or status.get("range_skew_date") or "—",
        )
        m3.metric("Scorecard Rows", len(scorecard) if not scorecard.empty else 0)

        if freshness.empty:
            st.info("No SPX freshness data available.")
        else:
            display_cols = [
                c
                for c in ["name", "exists", "modified_at", "age_hours"]
                if c in freshness.columns
            ]
            st.markdown("### SPX File Freshness")
            st.dataframe(freshness[display_cols], use_container_width=True, height=260)

    with right:
        st.markdown("## Options Algo V2")

        latest = options_loader.build_latest_scan_summary()
        paper_runs = options_loader.load_paper_live_runs()

        latest_scan_ok = bool(latest)
        paper_runs_ok = not paper_runs.empty
        data_root_ok = OPTIONS_ALGO_V2_DATA_ROOT.exists()

        c1, c2 = st.columns(2)
        with c1:
            _status_chip("Latest Scan", latest_scan_ok)
        with c2:
            _status_chip("Paper-Live Logs", paper_runs_ok)

        c3, c4 = st.columns(2)
        with c3:
            _status_chip("Options Data Root", data_root_ok)
        with c4:
            _state_chip(
                "Degraded Live Mode",
                bool(latest.get("degraded_live_mode")) if latest else False,
                true_text="Yes",
                false_text="No",
            )

        st.markdown("### Options Summary")

        o1, o2, o3 = st.columns(3)
        o1.metric("Run ID", latest.get("run_id", "—"))
        o2.metric("Passed", latest.get("total_passed", 0))
        o3.metric("Rejected", latest.get("total_rejected", 0))

        o4, o5, o6 = st.columns(3)
        o4.metric("Trade Ideas", latest.get("trade_idea_count", 0))
        o5.metric(
            "Top Candidates",
            len(latest.get("top_trade_candidate_symbols", [])),
        )
        o6.metric(
            "IV Ready Symbols",
            len(latest.get("iv_rank_ready_symbols", [])),
        )

        st.markdown("### Options Highlights")
        st.write(
            {
                "runtime_mode": latest.get("runtime_mode"),
                "as_of_date": latest.get("as_of_date"),
                "degraded_live_mode": latest.get("degraded_live_mode"),
                "top_trade_candidate_symbols": latest.get(
                    "top_trade_candidate_symbols",
                    [],
                ),
                "placeholder_iv_rank": latest.get(
                    "used_placeholder_iv_rank_inputs",
                    False,
                ),
            }
        )

        if not paper_runs.empty:
            st.markdown("### Recent Paper-Live Runs")
            display_cols = [
                col
                for col in [
                    "timestamp_utc",
                    "run_id",
                    "runtime_mode",
                    "passed_count",
                    "rejected_count",
                    "degraded_live_mode",
                ]
                if col in paper_runs.columns
            ]
            st.dataframe(
                paper_runs.tail(10)[display_cols],
                use_container_width=True,
                height=220,
            )
        else:
            st.info("No paper-live runs found for Options Algo V2.")

    st.divider()
    st.subheader("Quick Navigation")
    st.markdown(
        """
        - **SPX Daily Monitor** → latest predicted vs actual view
        - **SPX Forecasts** → latest forecast payload details
        - **SPX Comparison History** → scorecard and model tracking
        - **SPX Archive Browser** → archived forecast inspection
        - **Options Overview** → options scan artifacts, diagnostics, and paper-live logs
        - **Ops / Freshness** → file freshness / missing artifact checks
        """
    )
