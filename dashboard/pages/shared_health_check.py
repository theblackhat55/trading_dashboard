from __future__ import annotations

from pathlib import Path

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

    shared = load_shared_health()
    spx_monitor = shared.get("spx_monitoring", {})

    st.markdown(f"### Overall Status: {shared['overall_emoji']} {shared['overall'].upper()}")
    st.caption(f"Generated at: {shared['generated_at']}")

    if spx_monitor:
        st.subheader("SPX Monitoring Snapshot")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall", spx_monitor.get("overall_status_pill", "⚪ UNKNOWN"))
        c2.metric("Signal", spx_monitor.get("signal_status_pill", "⚪ UNKNOWN"))
        c3.metric("Forecast", spx_monitor.get("forecast_status_pill", "⚪ UNKNOWN"))
        c4.metric("Comparison", spx_monitor.get("comparison_status_pill", "⚪ UNKNOWN"))

        c5, c6 = st.columns(2)
        c5.metric("Drift", spx_monitor.get("drift_status_pill", "⚪ UNKNOWN"))
        c6.metric("Recommendation", spx_monitor.get("recommendation", "UNKNOWN"))

        monitor_health = spx_monitor.get("health", {})
        forecast_monitor = spx_monitor.get("forecast_monitor", {})
        retraining = spx_monitor.get("retraining", {})

        st.markdown("#### Current SPX State")
        st.json(
            {
                "signal_date": (monitor_health.get("signal") or {}).get("signal_date"),
                "forecast_for_date": (monitor_health.get("forecasts") or {}).get("forecast_for_date"),
                "generated_from_feature_date": (monitor_health.get("forecasts") or {}).get("generated_from_feature_date"),
                "drift_classification": spx_monitor.get("drift_classification"),
                "retraining_decision": retraining.get("decision"),
                "retraining_priority": retraining.get("priority"),
            }
        )

        reasons = []
        reasons.extend(monitor_health.get("reasons", []))
        reasons.extend(forecast_monitor.get("evidence", []))
        reasons.extend(retraining.get("reasons", []))

        if reasons:
            st.markdown("#### Reasons / Evidence")
            for r in reasons:
                st.write(f"- {r}")

        ops_md_path = Path("/root/spx_algo/output/monitoring/daily_ops_summary.md")
        st.markdown("#### LLM / Ops Summary")
        try:
            st.markdown(ops_md_path.read_text(encoding="utf-8"))
        except Exception as e:
            st.caption(f"Could not load ops summary: {e}")

    spx = shared["spx"]
    options = shared["options"]

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
        st.dataframe(_files_df(spx["files"], spx["buckets"]), width="stretch")

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
        st.dataframe(_files_df(options["files"], options["buckets"]), width="stretch")

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


if __name__ == "__main__":
    render()
