from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.loaders.spx_loader import (
    load_daily_comparison_report,
    load_daily_comparison_scorecard,
    list_comparison_report_dates,
)


def _pick(d: dict, *names, default=None):
    for n in names:
        if n in d:
            return d[n]
    return default


def render(spx_root):
    st.title("🎯 SPX Actual vs Predicted")

    dates = list_comparison_report_dates(spx_root)
    if not dates:
        st.warning("No comparison reports found yet.")
        return

    selected = st.selectbox("Select comparison date", dates)
    report = load_daily_comparison_report(spx_root, selected)
    if not report:
        st.error("Could not load comparison report.")
        return

    actual = report.get("actual_ohlc", {})
    hybrid_metrics = report.get("hybrid_metrics", {})
    rs_metrics = report.get("range_skew_metrics", {})

    hybrid_pred = (
        report.get("hybrid_predicted_ohlc")
        or report.get("hybrid_forecast_ohlc")
        or report.get("hybrid_ohlc")
        or {}
    )
    rs_pred = (
        report.get("range_skew_predicted_ohlc")
        or report.get("range_skew_forecast_ohlc")
        or report.get("range_skew_ohlc")
        or {}
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Date", selected)
    c2.metric("Hybrid Mean MAE", f"{float(_pick(hybrid_metrics, 'mean_ohlc_mae', default=0.0)):,.4f}")
    c3.metric("Range+Skew Mean MAE", f"{float(_pick(rs_metrics, 'mean_ohlc_mae', default=0.0)):,.4f}")

    def _num(x, k):
        try:
            return float(x.get(k, 0.0))
        except Exception:
            return 0.0

    fig = go.Figure()

    for label, src, color in [
        ("Actual", actual, "#22c55e"),
        ("Hybrid", hybrid_pred, "#3b82f6"),
        ("Range+Skew", rs_pred, "#f59e0b"),
    ]:
        if src:
            fig.add_trace(
                go.Bar(
                    name=label,
                    x=["Open", "High", "Low", "Close"],
                    y=[
                        _num(src, "open"),
                        _num(src, "high"),
                        _num(src, "low"),
                        _num(src, "close"),
                    ],
                    marker_color=color,
                )
            )

    fig.update_layout(
        barmode="group",
        height=480,
        margin=dict(l=20, r=20, t=30, b=20),
        title="Actual vs Predicted OHLC",
    )
    st.plotly_chart(fig, use_container_width=True)

    table = pd.DataFrame(
        [
            {
                "series": "Actual",
                "open": _num(actual, "open"),
                "high": _num(actual, "high"),
                "low": _num(actual, "low"),
                "close": _num(actual, "close"),
            },
            {
                "series": "Hybrid",
                "open": _num(hybrid_pred, "open"),
                "high": _num(hybrid_pred, "high"),
                "low": _num(hybrid_pred, "low"),
                "close": _num(hybrid_pred, "close"),
            },
            {
                "series": "Range+Skew",
                "open": _num(rs_pred, "open"),
                "high": _num(rs_pred, "high"),
                "low": _num(rs_pred, "low"),
                "close": _num(rs_pred, "close"),
            },
        ]
    )
    st.dataframe(table, use_container_width=True)

    scorecard = load_daily_comparison_scorecard(spx_root)
    if not scorecard.empty and "date" in scorecard.columns:
        scorecard["date"] = pd.to_datetime(scorecard["date"], errors="coerce")
        scorecard = scorecard.sort_values("date")

        rename_map = {
            "hybrid_mean_ohlc_mae": "Hybrid Mean MAE",
            "range_skew_mean_ohlc_mae": "Range+Skew Mean MAE",
            "hybrid_range_mae": "Hybrid Range MAE",
            "range_skew_range_mae": "Range+Skew Range MAE",
        }
        have = [c for c in rename_map if c in scorecard.columns]
        if have:
            plot_df = scorecard[["date"] + have].rename(columns=rename_map)
            fig2 = go.Figure()
            for col in plot_df.columns:
                if col == "date":
                    continue
                fig2.add_trace(
                    go.Scatter(
                        x=plot_df["date"],
                        y=plot_df[col],
                        mode="lines+markers",
                        name=col,
                    )
                )
            fig2.update_layout(
                height=420,
                margin=dict(l=20, r=20, t=30, b=20),
                title="Historical Error Trends",
            )
            st.plotly_chart(fig2, use_container_width=True)
