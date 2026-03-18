from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.config import OPTIONS_ALGO_V2_DATA_ROOT
from dashboard.loaders import options_loader
from dashboard.loaders.spx_loader import file_freshness


def _file_row(name: str, path: Path) -> dict[str, object]:
    exists = path.exists()
    modified_at = None
    age_hours = None

    if exists:
        stat = path.stat()
        modified_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        modified_at = modified_dt.isoformat()
        age_hours = (datetime.now(timezone.utc) - modified_dt).total_seconds() / 3600.0

    return {
        "name": name,
        "path": str(path),
        "exists": exists,
        "modified_at": modified_at,
        "age_hours": age_hours,
    }


def _options_freshness_df() -> pd.DataFrame:
    scan_dir = OPTIONS_ALGO_V2_DATA_ROOT / "scan_results"
    validation_dir = OPTIONS_ALGO_V2_DATA_ROOT / "validation"
    state_dir = OPTIONS_ALGO_V2_DATA_ROOT / "state"

    latest_scan = sorted(scan_dir.glob("scan_*.json"))
    latest_scan_path = latest_scan[-1] if latest_scan else scan_dir / "scan_latest.json"

    latest_summary = options_loader.build_latest_scan_summary()
    runs = options_loader.load_paper_live_runs()
    latest_run = {}
    if not runs.empty:
        latest_run = runs.sort_values(by="timestamp_utc", ascending=False).iloc[0].to_dict()

    rows = [
        {
            **_file_row("options_latest_scan", latest_scan_path),
            "latest_run_id": latest_summary.get("run_id"),
            "latest_as_of_date": latest_summary.get("as_of_date"),
            "latest_symbol_count": latest_summary.get("total_candidates"),
        },
        {
            **_file_row("options_paper_live_runs", validation_dir / "paper_live_runs.jsonl"),
            "latest_run_id": latest_run.get("run_id"),
            "latest_as_of_date": latest_run.get("as_of_date"),
            "latest_symbol_count": latest_run.get("symbol_count"),
        },
        {
            **_file_row("options_paper_live_symbol_decisions", validation_dir / "paper_live_symbol_decisions.jsonl"),
            "latest_run_id": latest_run.get("run_id"),
            "latest_as_of_date": latest_run.get("as_of_date"),
            "latest_symbol_count": latest_run.get("symbol_count"),
        },
        {
            **_file_row("options_iv_proxy_history", state_dir / "iv_proxy_history.jsonl"),
            "latest_run_id": None,
            "latest_as_of_date": latest_summary.get("as_of_date"),
            "latest_symbol_count": None,
        },
    ]
    return pd.DataFrame(rows)


def render(spx_root):
    st.title("🛠️ Ops / File Freshness")

    st.subheader("SPX Freshness")
    spx_df = file_freshness(spx_root)
    if spx_df.empty:
        st.warning("No tracked SPX files found.")
    else:
        st.dataframe(spx_df, use_container_width=True, height=300)

        stale = spx_df[
            (spx_df["exists"] == True)
            & (spx_df["age_hours"].notna())
            & (spx_df["age_hours"] > 24)
        ]
        missing = spx_df[spx_df["exists"] == False]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Missing SPX Files")
            if missing.empty:
                st.success("No missing tracked SPX files.")
            else:
                st.dataframe(missing, use_container_width=True)
        with col2:
            st.subheader("Stale SPX Files (>24h)")
            if stale.empty:
                st.success("No stale SPX files.")
            else:
                st.dataframe(stale, use_container_width=True)

    st.divider()

    st.subheader("Options Algo V2 Freshness")
    options_df = _options_freshness_df()
    if options_df.empty:
        st.warning("No tracked options files found.")
        return

    st.dataframe(options_df, use_container_width=True, height=240)

    stale_options = options_df[
        (options_df["exists"] == True)
        & (options_df["age_hours"].notna())
        & (options_df["age_hours"] > 24)
    ]
    missing_options = options_df[options_df["exists"] == False]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Missing Options Files")
        if missing_options.empty:
            st.success("No missing tracked options files.")
        else:
            st.dataframe(missing_options, use_container_width=True)

    with col2:
        st.subheader("Stale Options Files (>24h)")
        if stale_options.empty:
            st.success("No stale options files.")
        else:
            st.dataframe(stale_options, use_container_width=True)
