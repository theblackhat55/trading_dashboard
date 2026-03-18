from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.loaders.health_loader import load_shared_health


def _bucket_color(bucket: str) -> str:
    return {
        "ok": "#16a34a",
        "warn": "#ea580c",
        "bad": "#dc2626",
    }.get(bucket, "#6b7280")


def _render_status_pill(label: str, bucket: str) -> None:
    color = _bucket_color(bucket)
    st.markdown(
        f"""
        <span style="
            display:inline-block;
            padding:0.30rem 0.65rem;
            margin:0.15rem 0.35rem 0.15rem 0;
            border-radius:999px;
            background:{color};
            color:white;
            font-size:0.85rem;
            font-weight:600;
        ">{label}: {bucket.upper()}</span>
        """,
        unsafe_allow_html=True,
    )


def _files_df(files: dict, buckets: dict) -> pd.DataFrame:
    rows = []
    for name, info in files.items():
        rows.append(
            {
                "name": name,
                "status": buckets.get(name, "n/a"),
                "mtime": info.get("mtime_str"),
                "size": info.get("size"),
                "path": info.get("path"),
                "shape": info.get("shape"),
                "index_max": info.get("index_max"),
            }
        )
    return pd.DataFrame(rows)


def render() -> None:
    st.title("🩺 Shared Health Check")
    st.caption("Unified health and freshness checks for SPX Algo + Options Algo")

    health = load_shared_health()

    st.markdown(f"### Overall Status: {health['overall_emoji']} {health['overall'].upper()}")
    st.caption(f"Generated at: {health['generated_at']}")

    spx = health["spx"]
    options = health["options"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("SPX Algo")
        _render_status_pill("SPX Overall", spx["overall"])
        for name, bucket in spx["buckets"].items():
            _render_status_pill(name, bucket)

        signal = spx.get("signal") or {}
        hybrid = spx.get("hybrid") or {}
        range_skew = spx.get("range_skew") or {}

        st.markdown("#### Key Dates")
        st.write(
            {
                "signal_date": signal.get("signal_date"),
                "hybrid_forecast_for": hybrid.get("forecast_for_date"),
                "hybrid_generated_from": hybrid.get("generated_from_feature_date"),
                "range_skew_forecast_for": range_skew.get("forecast_for_date"),
                "range_skew_generated_from": range_skew.get("generated_from_feature_date"),
            }
        )

        st.markdown("#### SPX File Freshness")
        st.dataframe(_files_df(spx["files"], spx["buckets"]), use_container_width=True)

    with col2:
        st.subheader("Options Algo")
        _render_status_pill("Options Overall", options["overall"])
        for name, bucket in options["buckets"].items():
            _render_status_pill(name, bucket)

        st.markdown("#### Latest Options Payloads")
        st.write(
            {
                "latest_signal_keys": list((options.get("latest_signal") or {}).keys())[:12],
                "latest_scan_keys": list((options.get("latest_scan") or {}).keys())[:12],
                "latest_candidates_keys": list((options.get("latest_candidates") or {}).keys())[:12],
            }
        )

        st.markdown("#### Options File Freshness")
        st.dataframe(_files_df(options["files"], options["buckets"]), use_container_width=True)

    st.markdown("---")
    st.subheader("Quick Verdict Guide")
    st.markdown(
        """
- **OK**: fresh files and expected latest artifacts present
- **WARN**: files exist but look stale
- **BAD**: missing critical files or very stale artifacts

For SPX, the healthy morning state is usually:
- `latest_signal.json` on the current trading day
- `latest_gap_augmented_*forecast.json` generated from the current trading day
- forecast date set to the next trading day
- comparison scorecard updated after actuals become available
        """
    )



if __name__ == '__main__':
    render()
