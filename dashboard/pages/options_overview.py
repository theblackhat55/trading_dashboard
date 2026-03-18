from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.loaders import options_loader


def _dict_df(data: dict[str, object], key_name: str, value_name: str) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(columns=[key_name, value_name])
    rows = [{key_name: k, value_name: v} for k, v in data.items()]
    return pd.DataFrame(rows).sort_values(by=value_name, ascending=False)


def _symbol_list_df(symbols: list[str], column_name: str = "symbol") -> pd.DataFrame:
    return pd.DataFrame([{column_name: s} for s in symbols]) if symbols else pd.DataFrame(columns=[column_name])


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

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Run ID", latest.get("run_id", "—"))
    c2.metric("As Of", latest.get("as_of_date", "—"))
    c3.metric("Mode", latest.get("runtime_mode", "—"))
    c4.metric("Passed", latest.get("total_passed", 0))
    c5.metric("Rejected", latest.get("total_rejected", 0))
    c6.metric("Trade Ideas", latest.get("trade_idea_count", 0))

    c7, c8, c9, c10 = st.columns(4)
    c7.metric("Degraded Live Mode", "Yes" if latest.get("degraded_live_mode") else "No")
    c8.metric("Placeholder IV Rank", "Yes" if latest.get("used_placeholder_iv_rank_inputs") else "No")
    c9.metric("IV Ready Symbols", len(latest.get("iv_rank_ready_symbols", [])))
    c10.metric("Top Candidates", len(latest.get("top_trade_candidate_symbols", [])))

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.subheader("Top Trade Candidate Symbols")
        top_symbols_df = _symbol_list_df(latest.get("top_trade_candidate_symbols", []))
        if top_symbols_df.empty:
            st.info("No top trade candidate symbols.")
        else:
            st.dataframe(top_symbols_df, use_container_width=True, height=180)

        st.subheader("Rejection Reason Counts")
        rejection_df = _dict_df(latest.get("rejection_reason_counts", {}) or {}, "reason", "count")
        if rejection_df.empty:
            st.info("No rejection reasons found.")
        else:
            st.bar_chart(rejection_df.set_index("reason"))

        st.subheader("Signal State Counts")
        signal_df = _dict_df(latest.get("signal_state_counts", {}) or {}, "signal_state", "count")
        if signal_df.empty:
            st.info("No signal state counts.")
        else:
            st.bar_chart(signal_df.set_index("signal_state"))

    with right:
        st.subheader("Strategy Type Counts")
        strategy_df = _dict_df(latest.get("strategy_type_counts", {}) or {}, "strategy_type", "count")
        if strategy_df.empty:
            st.info("No strategy type counts.")
        else:
            st.bar_chart(strategy_df.set_index("strategy_type"))

        st.subheader("Quote Quality Counts")
        quote_df = _dict_df(latest.get("aggregate_quote_quality_counts", {}) or {}, "metric", "count")
        if quote_df.empty:
            st.info("No quote quality metrics.")
        else:
            st.dataframe(quote_df, use_container_width=True, height=250)

        st.subheader("IV Rank Readiness")
        ready_symbols = iv_readiness.get("ready_symbols", [])
        insufficient_symbols = iv_readiness.get("insufficient_history_symbols", [])
        st.write(
            {
                "ready_symbol_count": len(ready_symbols),
                "insufficient_history_symbol_count": len(insufficient_symbols),
                "iv_history_rows": iv_readiness.get("iv_history_rows", 0),
            }
        )
        readiness_counts = iv_readiness.get("observation_count_by_symbol", {}) or {}
        readiness_df = _dict_df(readiness_counts, "symbol", "observation_count")
        if readiness_df.empty:
            st.info("No IV rank readiness counts available.")
        else:
            st.dataframe(readiness_df, use_container_width=True, height=220)

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
        r2.metric("Average Pass Rate", f"{avg_pass_rate:.2%}" if isinstance(avg_pass_rate, float) else "—")
        r3.metric("Degraded Runs", recent_summary.get("degraded_live_mode_count", 0))
        r4.metric("Placeholder IV Rank Runs", recent_summary.get("used_placeholder_iv_rank_inputs_count", 0))

    if not paper_live_runs.empty:
        st.subheader("Recent Paper-Live Runs")
        runs = paper_live_runs.copy()
        for col in ["passed_symbols", "top_trade_candidate_symbols"]:
            if col in runs.columns:
                runs[col] = runs[col].apply(
                    lambda x: ", ".join(x) if isinstance(x, list) else x
                )
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
            if col in runs.columns
        ]
        st.dataframe(
            runs.sort_values(by="timestamp_utc", ascending=False)[display_cols].head(20),
            use_container_width=True,
            height=320,
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
        iv_cols = [col for col in ["as_of_date", "symbol", "implied_vol_proxy", "source"] if col in iv_history.columns]
        st.dataframe(iv_history.sort_values(by="as_of_date", ascending=False)[iv_cols].head(50), use_container_width=True, height=240)

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
