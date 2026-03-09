from __future__ import annotations

import streamlit as st

from dashboard.loaders.spx_loader import file_freshness


def render(spx_root):
    st.title("🛠️ Ops / File Freshness")

    df = file_freshness(spx_root)
    if df.empty:
        st.warning("No tracked files found.")
        return

    st.dataframe(df, use_container_width=True, height=420)

    stale = df[(df["exists"] == True) & (df["age_hours"].notna()) & (df["age_hours"] > 24)]
    missing = df[df["exists"] == False]

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Missing Files")
        if missing.empty:
            st.success("No missing tracked files.")
        else:
            st.dataframe(missing, use_container_width=True)

    with col2:
        st.subheader("Stale Files (>24h)")
        if stale.empty:
            st.success("No stale tracked files.")
        else:
            st.dataframe(stale, use_container_width=True)
