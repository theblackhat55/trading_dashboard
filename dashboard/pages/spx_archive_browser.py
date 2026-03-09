from __future__ import annotations

import json

import streamlit as st

from dashboard.loaders.spx_loader import (
    extract_ohlc,
    load_archived_forecast_by_name,
    load_forecast_archive,
    ohlc_summary,
)


def render(spx_root):
    st.title("🗂️ SPX Forecast Archive Browser")

    files = load_forecast_archive(spx_root)
    if not files:
        st.warning("No archived forecast files found.")
        return

    names = [p.name for p in files]
    selected = st.selectbox("Select archived forecast file", names)

    payload = load_archived_forecast_by_name(spx_root, selected)
    if not payload:
        st.error("Could not load selected archive file.")
        return

    st.caption(f"Selected file: {selected}")

    forecast_date = payload.get("forecast_for_date", "—")
    feature_date = payload.get("generated_from_feature_date", "—")
    source = payload.get("source_selection") or payload.get("component_source_selection") or "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("Forecast Date", forecast_date)
    c2.metric("Generated From", feature_date)
    c3.metric("Source Selection", str(source))

    ohlc = extract_ohlc(payload)
    summary = ohlc_summary(ohlc)

    if summary:
        a, b, c, d = st.columns(4)
        a.metric("Open", f"{summary['open']:,.2f}")
        b.metric("High", f"{summary['high']:,.2f}")
        c.metric("Low", f"{summary['low']:,.2f}")
        d.metric("Close", f"{summary['close']:,.2f}")

        e, f, g = st.columns(3)
        e.metric("Range", f"{summary['range']:,.2f}")
        f.metric("Up From Open", f"{summary['up_from_open']:,.2f}")
        g.metric("Down From Open", f"{summary['down_from_open']:,.2f}")

    overlay = payload.get("range_skew_overlay")
    if overlay:
        st.subheader("Range+Skew Overlay")
        st.json(overlay)

    st.subheader("Raw JSON")
    st.code(json.dumps(payload, indent=2), language="json")
