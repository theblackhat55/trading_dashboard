from __future__ import annotations

import json

import streamlit as st

from dashboard.loaders import options_loader


def _render_kv_dict(title: str, data: dict[str, object]) -> None:
    st.subheader(title)
    if not data:
        st.info("No data available.")
        return
    st.json(data)


def render():
    st.title("🧾 Options Overview")
    st.caption("Options Algo V2 scan artifacts, paper-live logs, and IV readiness")

    latest = options_loader.build_latest_scan_summary()
    candidates_df = options_loader.build_latest_trade_candidates_df()
    ideas_df = options_loader.build_latest_trade_ideas_df()
    recent_summary = options_loader.build_recent_paper_live_summary()
    leaderboard_df = options_loader.build_symbol_leaderboard_df()
    iv_readiness = options_loader.build_iv_rank_readiness_summary()
    latest_scan = options_loader.load_latest_scan()
    paper_live_runs = options_loader.load_paper_live_runs()
    iv_history = options_loader.load_iv_proxy_history()

    st.subheader("Latest Scan Status")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Run ID", latest.get("run_id", "—"))
    c2.metric("Runtime Mode", latest.get("runtime_mode", "—"))
    c3.metric("Passed", latest.get("total_passed", 0))
    c4.metric("Rejected", latest.get("total_rejected", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Trade Ideas", latest.get("trade_idea_count", 0))
    c6.metric("Degraded Live Mode", "Yes" if latest.get("degraded_live_mode") else "No")
    c7.metric(
        "Placeholder IV Rank",
        "Yes" if latest.get("used_placeholder_iv_rank_inputs") else "No",
    )
    c8.metric("IV Ready Symbols", len(latest.get("iv_rank_ready_symbols", [])))

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        _render_kv_dict(
            "Top Trade Candidate Symbols",
            {"symbols": latest.get("top_trade_candidate_symbols", [])},
        )
        _render_kv_dict(
            "Rejection Reason Counts",
            latest.get("rejection_reason_counts", {}) or {},
        )
        _render_kv_dict(
            "Signal State Counts",
            latest.get("signal_state_counts", {}) or {},
        )

    with right:
        _render_kv_dict(
            "Strategy Type Counts",
            latest.get("strategy_type_counts", {}) or {},
        )
        _render_kv_dict(
            "Quote Quality Counts",
            latest.get("aggregate_quote_quality_counts", {}) or {},
        )
        _render_kv_dict(
            "IV Rank Readiness",
            {
                "ready_symbols": iv_readiness.get("ready_symbols", []),
                "insufficient_history_symbols": iv_readiness.get(
                    "insufficient_history_symbols",
                    [],
                ),
                "observation_count_by_symbol": iv_readiness.get(
                    "observation_count_by_symbol",
                    {},
                ),
            },
        )

    st.markdown("---")

    st.subheader("Latest Trade Candidates")
    if candidates_df.empty:
        st.info("No trade candidates found in latest scan.")
    else:
        st.dataframe(candidates_df, use_container_width=True, height=260)

    st.subheader("Latest Trade Ideas")
    if ideas_df.empty:
        st.info("No trade ideas found in latest scan.")
    else:
        st.dataframe(ideas_df, use_container_width=True, height=240)

    st.markdown("---")

    st.subheader("Paper-Live Summary")
    if not recent_summary:
        st.info("No paper-live run summary available.")
    else:
        r1, r2, r3, r4 = st.columns(4)
        avg_pass_rate = recent_summary.get("average_pass_rate")
        r1.metric("Run Count", recent_summary.get("run_count", 0))
        r2.metric(
            "Average Pass Rate",
            f"{avg_pass_rate:.2%}" if isinstance(avg_pass_rate, float) else "—",
        )
        r3.metric(
            "Degraded Runs",
            recent_summary.get("degraded_live_mode_count", 0),
        )
        r4.metric(
            "Placeholder IV Rank Runs",
            recent_summary.get("used_placeholder_iv_rank_inputs_count", 0),
        )

    if not paper_live_runs.empty:
        st.subheader("Recent Paper-Live Runs")
        display_cols = [
            col
            for col in [
                "timestamp_utc",
                "run_id",
                "runtime_mode",
                "as_of_date",
                "strict_live_mode",
                "degraded_live_mode",
                "symbol_count",
                "passed_count",
                "rejected_count",
                "passed_symbols",
                "top_trade_candidate_symbols",
            ]
            if col in paper_live_runs.columns
        ]
        st.dataframe(
            paper_live_runs.tail(20)[display_cols],
            use_container_width=True,
            height=260,
        )
    else:
        st.info("No paper-live run log found.")

    st.markdown("---")

    st.subheader("Symbol Leaderboard")
    if leaderboard_df.empty:
        st.info("No symbol decision history found.")
    else:
        st.dataframe(leaderboard_df, use_container_width=True, height=320)

    st.markdown("---")

    st.subheader("IV Proxy History")
    if iv_history.empty:
        st.info("No IV proxy history found.")
    else:
        iv_cols = [
            col
            for col in ["as_of_date", "symbol", "implied_vol_proxy", "source"]
            if col in iv_history.columns
        ]
        st.dataframe(iv_history.tail(50)[iv_cols], use_container_width=True, height=240)

    with st.expander("Latest Scan JSON"):
        if latest_scan:
            st.json(latest_scan)
        else:
            st.info("No latest scan artifact found.")

    with st.expander("Liquidity Debug by Symbol"):
        if latest_scan:
            runtime_metadata = latest_scan.get("runtime_metadata", {})
            st.json(runtime_metadata.get("liquidity_debug_by_symbol", {}))
        else:
            st.info("No latest scan artifact found.")

    with st.expander("Quote Quality by Symbol"):
        if latest_scan:
            runtime_metadata = latest_scan.get("runtime_metadata", {})
            st.json(runtime_metadata.get("quote_quality_by_symbol", {}))
        else:
            st.info("No latest scan artifact found.")
