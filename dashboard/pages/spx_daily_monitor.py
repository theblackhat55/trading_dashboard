from __future__ import annotations

import json

import streamlit as st
import plotly.graph_objects as go

from dashboard.loaders.spx_loader import (
    extract_ohlc,
    latest_forecast_status,
    load_daily_comparison_report,
    load_latest_hybrid_forecast,
    load_latest_range_skew_forecast,
    ohlc_summary,
)


def _badge(status: str) -> None:
    color = {
        "Compared": "green",
        "Awaiting Actuals": "orange",
        "Missing Files": "red",
        "Partial Forecast Set": "orange",
        "Forecast Date Mismatch": "red",
    }.get(status, "blue")
    st.markdown(
        f"""
        <div style="
            display:inline-block;
            padding:0.35rem 0.75rem;
            border-radius:999px;
            background:{color};
            color:white;
            font-weight:600;
            margin-bottom:1rem;">
            {status}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(spx_root):
    st.title("📈 SPX Daily Monitor")

    status = latest_forecast_status(spx_root)
    _badge(status["status"])

    hybrid_payload = load_latest_hybrid_forecast(spx_root)
    rs_payload = load_latest_range_skew_forecast(spx_root)

    hybrid_ohlc = extract_ohlc(hybrid_payload)
    rs_ohlc = extract_ohlc(rs_payload)

    hybrid = ohlc_summary(hybrid_ohlc)
    rs = ohlc_summary(rs_ohlc)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hybrid Forecast Date", status.get("hybrid_date") or "—")
    c2.metric("Range+Skew Forecast Date", status.get("range_skew_date") or "—")
    c3.metric("Hybrid File Updated", status.get("hybrid_mtime") or "—")
    c4.metric("Range+Skew File Updated", status.get("range_skew_mtime") or "—")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Hybrid Forecast")
        if hybrid:
            a, b, c = st.columns(3)
            a.metric("Open", f"{hybrid['open']:,.2f}")
            b.metric("High", f"{hybrid['high']:,.2f}")
            c.metric("Low", f"{hybrid['low']:,.2f}")
            d, e, f = st.columns(3)
            d.metric("Close", f"{hybrid['close']:,.2f}")
            e.metric("Range", f"{hybrid['range']:,.2f}")
            f.metric("Up From Open", f"{hybrid['up_from_open']:,.2f}")
            st.caption(f"Down From Open: {hybrid['down_from_open']:.2f}")
        else:
            st.warning("Hybrid forecast not available.")

    with right:
        st.subheader("Range+Skew Forecast")
        if rs:
            a, b, c = st.columns(3)
            a.metric("Open", f"{rs['open']:,.2f}")
            b.metric("High", f"{rs['high']:,.2f}")
            c.metric("Low", f"{rs['low']:,.2f}")
            d, e, f = st.columns(3)
            d.metric("Close", f"{rs['close']:,.2f}")
            e.metric("Range", f"{rs['range']:,.2f}")
            f.metric("Up From Open", f"{rs['up_from_open']:,.2f}")
            st.caption(f"Down From Open: {rs['down_from_open']:.2f}")
        else:
            st.warning("Range+Skew forecast not available.")

    if hybrid and rs:
        st.divider()
        st.subheader("Range Comparison")

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Hybrid",
                x=["Down From Open", "Up From Open", "Total Range"],
                y=[
                    hybrid["down_from_open"],
                    hybrid["up_from_open"],
                    hybrid["range"],
                ],
            )
        )
        fig.add_trace(
            go.Bar(
                name="Range+Skew",
                x=["Down From Open", "Up From Open", "Total Range"],
                y=[
                    rs["down_from_open"],
                    rs["up_from_open"],
                    rs["range"],
                ],
            )
        )
        fig.update_layout(
            barmode="group",
            height=420,
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    report_date = status.get("hybrid_date")
    report = load_daily_comparison_report(spx_root, report_date) if report_date else None

    st.divider()
    st.subheader("Actuals & Comparison")

    if report:
        actual = report.get("actual_ohlc", {})
        hybrid_metrics = report.get("hybrid_metrics", {})
        rs_metrics = report.get("range_skew_metrics", {})

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Actual Open", f"{float(actual.get('open', 0.0)):,.2f}")
        a2.metric("Actual High", f"{float(actual.get('high', 0.0)):,.2f}")
        a3.metric("Actual Low", f"{float(actual.get('low', 0.0)):,.2f}")
        a4.metric("Actual Close", f"{float(actual.get('close', 0.0)):,.2f}")

        b1, b2, b3 = st.columns(3)
        hybrid_mae = float(hybrid_metrics.get("mean_ohlc_mae", 0.0))
        rs_mae = float(rs_metrics.get("mean_ohlc_mae", 0.0))
        b1.metric("Hybrid Mean OHLC MAE", f"{hybrid_mae:,.4f}")
        b2.metric("Range+Skew Mean OHLC MAE", f"{rs_mae:,.4f}")
        b3.metric("Lower Mean MAE", "Hybrid" if hybrid_mae < rs_mae else "Range+Skew")

        c1, c2, c3 = st.columns(3)
        hybrid_range = float(hybrid_metrics.get("range_mae", 0.0))
        rs_range = float(rs_metrics.get("range_mae", 0.0))
        c1.metric("Hybrid Range Error", f"{hybrid_range:,.4f}")
        c2.metric("Range+Skew Range Error", f"{rs_range:,.4f}")

        h_cov = float(hybrid_metrics.get("inside_range_coverage", 0.0))
        r_cov = float(rs_metrics.get("inside_range_coverage", 0.0))
        if h_cov > r_cov:
            coverage_winner = "Hybrid"
        elif r_cov > h_cov:
            coverage_winner = "Range+Skew"
        else:
            coverage_winner = "Tie"
        c3.metric("Coverage Winner", coverage_winner)
    else:
        st.info("Actual OHLC comparison report is not available yet for the latest forecast date.")

    with st.expander("Raw Hybrid Forecast JSON"):
        st.code(json.dumps(hybrid_payload or {}, indent=2), language="json")

    with st.expander("Raw Range+Skew Forecast JSON"):
        st.code(json.dumps(rs_payload or {}, indent=2), language="json")
