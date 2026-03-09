from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.loaders import spx_loader


def _fmt(v: float | None) -> str:
    return "N/A" if v is None else f"{v:,.2f}"


def render():
    st.title("📈 SPX Forecasts")

    hybrid_payload = spx_loader.load_latest_hybrid_forecast()
    rs_payload = spx_loader.load_latest_range_skew_forecast()

    hybrid_ohlc = spx_loader.ohlc_summary(spx_loader.extract_ohlc(hybrid_payload))
    rs_ohlc = spx_loader.ohlc_summary(spx_loader.extract_ohlc(rs_payload))

    if not hybrid_payload and not rs_payload:
        st.warning("No SPX forecast files found.")
        return

    forecast_date = None
    feature_date = None
    if rs_payload:
        forecast_date = rs_payload.get("forecast_for_date")
        feature_date = rs_payload.get("generated_from_feature_date")
    elif hybrid_payload:
        forecast_date = hybrid_payload.get("forecast_for_date")
        feature_date = hybrid_payload.get("generated_from_feature_date")

    c1, c2 = st.columns(2)
    c1.metric("Forecast Date", forecast_date or "N/A")
    c2.metric("Generated From", feature_date or "N/A")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Hybrid Forecast")
        if hybrid_ohlc:
            m1, m2, m3 = st.columns(3)
            m1.metric("Open", _fmt(hybrid_ohlc["open"]))
            m2.metric("High", _fmt(hybrid_ohlc["high"]))
            m3.metric("Low", _fmt(hybrid_ohlc["low"]))

            m4, m5, m6 = st.columns(3)
            m4.metric("Close", _fmt(hybrid_ohlc["close"]))
            m5.metric("Range", _fmt(hybrid_ohlc["range"]))
            m6.metric("Up From Open", _fmt(hybrid_ohlc["up_from_open"]))

    with col2:
        st.subheader("Range+Skew Forecast")
        if rs_ohlc:
            m1, m2, m3 = st.columns(3)
            m1.metric("Open", _fmt(rs_ohlc["open"]))
            m2.metric("High", _fmt(rs_ohlc["high"]))
            m3.metric("Low", _fmt(rs_ohlc["low"]))

            m4, m5, m6 = st.columns(3)
            m4.metric("Close", _fmt(rs_ohlc["close"]))
            m5.metric("Range", _fmt(rs_ohlc["range"]))
            m6.metric("Up From Open", _fmt(rs_ohlc["up_from_open"]))

    if rs_payload and rs_payload.get("range_skew_overlay"):
        st.markdown("---")
        st.subheader("Range+Skew Overlay")
        overlay = rs_payload["range_skew_overlay"]

        o1, o2, o3 = st.columns(3)
        o1.metric("Pred Range", _fmt(overlay.get("pred_range")))
        o2.metric("Raw Up Share", f"{overlay.get('pred_up_share_raw', 0):.6f}")
        o3.metric("Blended Up Share", f"{overlay.get('pred_up_share_blended', 0):.6f}")

        o4, o5, o6 = st.columns(3)
        o4.metric("Clipped Up Share", f"{overlay.get('pred_up_share_model_clipped', 0):.6f}")
        o5.metric("Hybrid Up Share", f"{overlay.get('hybrid_up_share', 0):.6f}")
        o6.metric("Skew Alpha", f"{overlay.get('skew_alpha', 0):.2f}")

    if hybrid_ohlc or rs_ohlc:
        st.markdown("---")
        st.subheader("Forecast Range Visualization")

        fig = go.Figure()

        if hybrid_ohlc:
            fig.add_trace(go.Bar(
                x=["Hybrid"],
                y=[hybrid_ohlc["range"]],
                base=[hybrid_ohlc["low"]],
                name="Hybrid Range",
            ))

        if rs_ohlc:
            fig.add_trace(go.Bar(
                x=["Range+Skew"],
                y=[rs_ohlc["range"]],
                base=[rs_ohlc["low"]],
                name="Range+Skew Range",
            ))

        fig.update_layout(
            height=450,
            yaxis_title="SPX Price",
            barmode="group",
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Raw Forecast Payloads")

    with st.expander("Hybrid JSON", expanded=False):
        st.json(hybrid_payload or {})

    with st.expander("Range+Skew JSON", expanded=False):
        st.json(rs_payload or {})
