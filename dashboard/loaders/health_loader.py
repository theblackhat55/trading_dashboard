from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

SPX_ROOT = Path("/root/spx_algo")
OPTIONS_ROOT = Path("/root/options_algo")


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _file_info(path: Path) -> dict[str, Any]:
    if not path.exists() and not path.is_symlink():
        return {
            "exists": False,
            "path": str(path),
            "mtime": None,
            "mtime_str": "missing",
            "size": None,
        }
    try:
        st = path.stat()
        return {
            "exists": True,
            "path": str(path),
            "mtime": st.st_mtime,
            "mtime_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
            "size": st.st_size,
        }
    except Exception:
        return {
            "exists": False,
            "path": str(path),
            "mtime": None,
            "mtime_str": "error",
            "size": None,
        }


def _parquet_info(path: Path) -> dict[str, Any]:
    base = _file_info(path)
    if not base["exists"]:
        base["shape"] = None
        base["index_max"] = None
        return base

    try:
        df = pd.read_parquet(path)
        base["shape"] = tuple(df.shape)
        if "date" in df.columns:
            base["index_max"] = str(df["date"].max())
        else:
            base["index_max"] = str(df.index.max())
    except Exception as e:
        base["shape"] = None
        base["index_max"] = f"error: {e}"
    return base


def _age_bucket(mtime: float | None, warn_hours: float = 12, bad_hours: float = 36) -> str:
    if mtime is None:
        return "bad"
    age_hours = (time.time() - mtime) / 3600.0
    if age_hours <= warn_hours:
        return "ok"
    if age_hours <= bad_hours:
        return "warn"
    return "bad"


def _status_emoji(bucket: str) -> str:
    return {"ok": "🟢", "warn": "🟠", "bad": "🔴"}.get(bucket, "⚪")


def load_spx_health(spx_root: Path | None = None) -> dict[str, Any]:
    spx_root = spx_root or SPX_ROOT

    signal_path = spx_root / "output/signals/latest_signal.json"
    hybrid_path = spx_root / "output/forecasts/latest_gap_augmented_hybrid_ohlc_forecast.json"
    range_path = spx_root / "output/forecasts/latest_gap_augmented_range_skew_forecast.json"
    scorecard_path = spx_root / "output/reports/daily_forecast_comparison/daily_hybrid_vs_range_skew_scorecard.csv"

    signal = _safe_read_json(signal_path)
    hybrid = _safe_read_json(hybrid_path)
    range_skew = _safe_read_json(range_path)

    files = {
        "latest_signal": _file_info(signal_path),
        "hybrid_forecast": _file_info(hybrid_path),
        "range_skew_forecast": _file_info(range_path),
        "comparison_scorecard": _file_info(scorecard_path),
        "features_parquet": _parquet_info(spx_root / "data/processed/features.parquet"),
        "es_overnight_features": _parquet_info(spx_root / "data/processed/es_overnight_features.parquet"),
        "es_databento_overnight_features": _parquet_info(spx_root / "data/processed/es_databento_overnight_features.parquet"),
        "spx_daily_raw": _parquet_info(spx_root / "data/raw/spx_daily.parquet"),
        "vix_daily_raw": _parquet_info(spx_root / "data/raw/vix_daily.parquet"),
        "es_daily_raw": _parquet_info(spx_root / "data/raw/es_daily.parquet"),
        "es_5m_recent_raw": _parquet_info(spx_root / "data/raw/es_5m_recent.parquet"),
        "es_databento_1m_raw": _parquet_info(spx_root / "data/raw/es_databento_1m.parquet"),
    }

    buckets = {
        name: _age_bucket(info.get("mtime"))
        for name, info in files.items()
        if "mtime" in info
    }

    overall = "ok"
    if any(v == "bad" for v in buckets.values()):
        overall = "bad"
    elif any(v == "warn" for v in buckets.values()):
        overall = "warn"

    return {
        "overall": overall,
        "overall_emoji": _status_emoji(overall),
        "signal": signal,
        "hybrid": hybrid,
        "range_skew": range_skew,
        "files": files,
        "buckets": buckets,
    }


def load_options_health(options_root: Path | None = None) -> dict[str, Any]:
    options_root = options_root or OPTIONS_ROOT

    candidates = {
        "latest_signal": options_root / "output/signals/options_signal_latest.json",
        "latest_options_signal": options_root / "output/signals/options_signal_latest.json",
        "trade_outcomes_log": options_root / "output/trades/trade_outcomes.jsonl",
        "latest_papertrade_log": options_root / "output/trades/trade_outcomes.jsonl",
        "options_data_root": options_root / "output",
    }

    files = {name: _file_info(path) for name, path in candidates.items()}
    buckets = {
        name: _age_bucket(info.get("mtime"))
        for name, info in files.items()
        if "mtime" in info
    }

    overall = "ok"
    if any(v == "bad" for v in buckets.values()):
        overall = "bad"
    elif any(v == "warn" for v in buckets.values()):
        overall = "warn"

    latest_signal = _safe_read_json(candidates["latest_signal"])
    latest_scan = _safe_read_json(candidates["latest_options_signal"])
    latest_candidates = None

    return {
        "overall": overall,
        "overall_emoji": _status_emoji(overall),
        "latest_signal": latest_signal,
        "latest_scan": latest_scan,
        "latest_candidates": latest_candidates,
        "files": files,
        "buckets": buckets,
    }


def load_shared_health() -> dict[str, Any]:
    spx = load_spx_health()
    options = load_options_health()

    overall = "ok"
    if spx["overall"] == "bad" or options["overall"] == "bad":
        overall = "bad"
    elif spx["overall"] == "warn" or options["overall"] == "warn":
        overall = "warn"

    return {
        "overall": overall,
        "overall_emoji": _status_emoji(overall),
        "spx": spx,
        "options": options,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
