from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from dashboard.config import OPTIONS_ALGO_V2_DATA_ROOT, SPX_ALGO_ROOT


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        with open(path, "r") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _safe_read_jsonl_last(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        last: dict[str, Any] | None = None
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict):
                    last = obj
        return last
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
    spx_root = spx_root or SPX_ALGO_ROOT

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


def load_options_health(options_data_root: Path | None = None) -> dict[str, Any]:
    data_root = options_data_root or OPTIONS_ALGO_V2_DATA_ROOT
    scan_dir = data_root / "scan_results"
    validation_dir = data_root / "validation"
    state_dir = data_root / "state"

    scan_files = sorted(scan_dir.glob("scan_*.json"))
    latest_scan_path = scan_files[-1] if scan_files else scan_dir / "scan_latest.json"

    runs_path = validation_dir / "paper_live_runs.jsonl"
    symbol_decisions_path = validation_dir / "paper_live_symbol_decisions.jsonl"
    iv_history_path = state_dir / "iv_proxy_history.jsonl"

    files = {
        "latest_scan": _file_info(latest_scan_path),
        "paper_live_runs": _file_info(runs_path),
        "paper_live_symbol_decisions": _file_info(symbol_decisions_path),
        "iv_proxy_history": _file_info(iv_history_path),
    }

    buckets = {
        name: _age_bucket(info.get("mtime"))
        for name, info in files.items()
        if "mtime" in info
    }

    latest_scan = _safe_read_json(latest_scan_path)
    latest_run = _safe_read_jsonl_last(runs_path)

    latest_candidates: dict[str, Any] | None = None
    if isinstance(latest_scan, dict):
        latest_candidates = {
            "trade_candidates_count": len(latest_scan.get("trade_candidates", []) or []),
            "trade_ideas_count": len(latest_scan.get("trade_ideas", []) or []),
        }

    overall = "ok"
    if any(v == "bad" for v in buckets.values()):
        overall = "bad"
    elif any(v == "warn" for v in buckets.values()):
        overall = "warn"

    return {
        "overall": overall,
        "overall_emoji": _status_emoji(overall),
        "latest_signal": latest_run,
        "latest_scan": latest_scan,
        "latest_candidates": latest_candidates,
        "files": files,
        "buckets": buckets,
        "data_root": str(data_root),
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
