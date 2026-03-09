from __future__ import annotations

import streamlit as st

from dashboard.loaders import options_loader


def render():
    st.title("🧾 Options Overview")

    sig = options_loader.load_latest_options_signal()
    positions = options_loader.load_positions()
    outcomes = options_loader.load_trade_outcomes()

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest Signal", "✅" if sig else "❌")

    pos_count = 0
    if isinstance(positions, list):
        pos_count = len(positions)
    elif isinstance(positions, dict):
        pos_count = len(positions)
    c2.metric("Positions", pos_count)

    c3.metric("Trade Outcomes", len(outcomes) if not outcomes.empty else 0)

    st.markdown("---")

    if sig:
        st.subheader("Latest Options Signal")
        st.json(sig)
    else:
        st.info("No latest options signal found.")

    st.markdown("---")

    st.subheader("Positions")
    if positions:
        st.json(positions)
    else:
        st.info("No positions file found or empty.")

    st.markdown("---")

    st.subheader("Trade Outcomes")
    if not outcomes.empty:
        st.dataframe(outcomes.tail(50), use_container_width=True)
    else:
        st.info("No trade outcomes found.")
