from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.loaders.spx_loader import load_daily_comparison_scorecard


def render(spx_root):
    st.title("📊 SPX Comparison History")

    df = load_daily_comparison_scorecard(spx_root)
    if df.empty:
        st.warning("No comparison scorecard found yet.")
        return

    st.caption(f"Rows: {len(df)}")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")

    numeric_candidates = [
        "hybrid_mean_ohlc_mae",
        "range_skew_mean_ohlc_mae",
        "hybrid_range_mae",
        "range_skew_range_mae",
        "hybrid_inside_range_coverage",
        "range_skew_inside_range_coverage",
    ]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    top1, top2, top3, top4 = st.columns(4)

    if {"hybrid_mean_ohlc_mae", "range_skew_mean_ohlc_mae"}.issubset(df.columns):
        hybrid_wins = int((df["hybrid_mean_ohlc_mae"] < df["range_skew_mean_ohlc_mae"]).sum())
        rs_wins = int((df["range_skew_mean_ohlc_mae"] < df["hybrid_mean_ohlc_mae"]).sum())
        ties = int((df["range_skew_mean_ohlc_mae"] == df["hybrid_mean_ohlc_mae"]).sum())
        top1.metric("Hybrid Mean-MAE Wins", hybrid_wins)
        top2.metric("Range+Skew Mean-MAE Wins", rs_wins)
        top3.metric("Ties", ties)

    if "range_skew_mean_ohlc_mae" in df.columns:
        latest = df["range_skew_mean_ohlc_mae"].dropna()
        top4.metric("Latest Range+Skew Mean MAE", f"{latest.iloc[-1]:,.4f}" if not latest.empty else "—")

    st.divider()

    if {"date", "hybrid_mean_ohlc_mae", "range_skew_mean_ohlc_mae"}.issubset(df.columns):
        plot_df = df[["date", "hybrid_mean_ohlc_mae", "range_skew_mean_ohlc_mae"]].dropna()
        if not plot_df.empty:
            fig = px.line(
                plot_df,
                x="date",
                y=["hybrid_mean_ohlc_mae", "range_skew_mean_ohlc_mae"],
                markers=True,
                title="Mean OHLC MAE Over Time",
            )
            st.plotly_chart(fig, use_container_width=True)

    if {"date", "hybrid_range_mae", "range_skew_range_mae"}.issubset(df.columns):
        plot_df = df[["date", "hybrid_range_mae", "range_skew_range_mae"]].dropna()
        if not plot_df.empty:
            fig = px.line(
                plot_df,
                x="date",
                y=["hybrid_range_mae", "range_skew_range_mae"],
                markers=True,
                title="Range Error Over Time",
            )
            st.plotly_chart(fig, use_container_width=True)

    if {"date", "hybrid_inside_range_coverage", "range_skew_inside_range_coverage"}.issubset(df.columns):
        plot_df = df[["date", "hybrid_inside_range_coverage", "range_skew_inside_range_coverage"]].dropna()
        if not plot_df.empty:
            fig = px.bar(
                plot_df,
                x="date",
                y=["hybrid_inside_range_coverage", "range_skew_inside_range_coverage"],
                barmode="group",
                title="Inside-Range Coverage by Day",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Scorecard Table")
    st.dataframe(df, use_container_width=True, height=500)
