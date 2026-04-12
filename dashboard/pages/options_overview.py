from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.loaders import options_v2_sqlite


def render() -> None:
    st.title("🧾 Options Overview")
    st.caption("SQLite-first monitoring for options_algo_v2")

    db_status = options_v2_sqlite.get_db_status()
    latest_run_id = options_v2_sqlite.get_latest_run_id()
    latest_run_summary = options_v2_sqlite.get_latest_run_summary()
    rescue_summary = options_v2_sqlite.get_rescue_summary(limit_runs=20)
    overlap_anomalies = options_v2_sqlite.get_overlap_anomaly_count()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest Run ID", latest_run_id or "n/a")
    c2.metric("DB Exists", "Yes" if db_status["exists"] else "No")
    c3.metric("Tier A Rescues (20 runs)", rescue_summary["tier_a_count"])
    c4.metric("Overlap Anomalies", overlap_anomalies)

    c5, c6, c7 = st.columns(3)
    c5.metric("Tier B Rescues (20 runs)", rescue_summary["tier_b_count"])
    c6.metric("Rescued Passes (20 runs)", rescue_summary["rescued_pass_count"])
    c7.metric("Normal Passes (20 runs)", rescue_summary["normal_pass_count"])

    with st.expander("DB status / latest summary", expanded=False):
        st.write(db_status)
        st.write(latest_run_summary)

    if overlap_anomalies:
        st.error(
            f"Found {overlap_anomalies} rows with overlapping Tier A and Tier B flags."
        )
    else:
        st.success("No overlapping Tier A / Tier B rescue flags detected.")

    st.subheader("Latest symbol decisions")
    latest_df = options_v2_sqlite.get_latest_symbol_rows(limit=200)

    if latest_df.empty:
        st.warning("No latest symbol rows found in SQLite.")
    else:
        display_df = latest_df.copy()

        for col in [
            "options_context_effective_soft_penalties_json",
            "blocking_reasons_json",
            "soft_penalty_reasons_json",
        ]:
            if col in display_df.columns:
                display_df[col] = display_df[col].fillna("[]")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        rescued_df = display_df[
            display_df["options_context_borderline_score_pass"].fillna(0).astype(int) == 1
        ]
        if not rescued_df.empty:
            st.subheader("Latest rescued rows")
            st.dataframe(rescued_df, use_container_width=True, hide_index=True)

    st.subheader("Recent rescue concentration")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Top Tier A symbols (20 runs)**")
        st.dataframe(
            pd.DataFrame(rescue_summary["top_tier_a_symbols"]),
            use_container_width=True,
            hide_index=True,
        )
    with col_b:
        st.markdown("**Top Tier B symbols (20 runs)**")
        st.dataframe(
            pd.DataFrame(rescue_summary["top_tier_b_symbols"]),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Recent history for showcase symbols")
    showcase_symbols = st.multiselect(
        "Symbols",
        options=["BAC", "NFLX", "CRM", "ORCL", "XLE", "AMD", "AVGO", "SMH"],
        default=["BAC", "NFLX", "CRM"],
    )
    history_df = options_v2_sqlite.get_recent_symbol_history(
        showcase_symbols,
        limit_runs=20,
    )

    if history_df.empty:
        st.info("No recent history found for selected symbols.")
    else:
        st.dataframe(history_df, use_container_width=True, hide_index=True)
