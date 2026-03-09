from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_SPX_ROOT = Path(os.getenv("SPX_ALGO_ROOT", "/root/spx_algo"))


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text())
    except Exception:
        return None


def _safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _safe_read_parquet(path: Path) -> pd.DataFrame:
    try:
        if not path.exists():
            return pd.DataFrame()
        return pd.read_parquet(path)
    except Exception:
        return pd.DataFrame()


def _mtime(path: Path) -> str | None:
    try:
        if not path.exists():
            return None
        return pd.Timestamp(path.stat().st_mtime, unit="s").isoformat()
    except Exception:
        return None


def extract_ohlc(payload: dict[str, Any] | None) -> dict[str, float] | None:
    if not payload:
        return None

    candidates = [
        payload.get("predicted_ohlc"),
        payload.get("hybrid_predicted_ohlc"),
        payload.get("final_predicted_ohlc"),
        payload.get("predicted_values"),
        payload,
    ]

    for block in candidates:
        if not isinstance(block, dict):
            continue

        if all(k in block for k in ("open", "high", "low", "close")):
            return {
                "open": float(block["open"]),
                "high": float(block["high"]),
                "low": float(block["low"]),
                "close": float(block["close"]),
            }

        prefixed = ("pred_open", "pred_high", "pred_low", "pred_close")
        if all(k in block for k in prefixed):
            return {
                "open": float(block["pred_open"]),
                "high": float(block["pred_high"]),
                "low": float(block["pred_low"]),
                "close": float(block["pred_close"]),
            }

    return None


def ohlc_summary(ohlc: dict[str, float] | None) -> dict[str, float] | None:
    if not ohlc:
        return None
    op = float(ohlc["open"])
    hi = float(ohlc["high"])
    lo = float(ohlc["low"])
    cl = float(ohlc["close"])
    return {
        "open": op,
        "high": hi,
        "low": lo,
        "close": cl,
        "range": hi - lo,
        "up_from_open": hi - op,
        "down_from_open": op - lo,
        "close_change": cl - op,
    }


def load_spx_daily(spx_root: Path | None = None) -> pd.DataFrame:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    return _safe_read_parquet(spx_root / "data/raw/spx_daily.parquet")


def load_vix_daily(spx_root: Path | None = None) -> pd.DataFrame:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    return _safe_read_parquet(spx_root / "data/raw/vix_daily.parquet")


def load_latest_signal(spx_root: Path | None = None) -> dict[str, Any] | None:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    return _safe_read_json(spx_root / "output/signals/latest_signal.json")


def load_paper_trade_log(spx_root: Path | None = None) -> pd.DataFrame:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    return _safe_read_csv(spx_root / "output/trades/paper_trade_log.csv")


def load_latest_hybrid_forecast(spx_root: Path | None = None) -> dict[str, Any] | None:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    return _safe_read_json(
        spx_root / "output/forecasts/latest_gap_augmented_hybrid_ohlc_forecast.json"
    )


def load_latest_range_skew_forecast(spx_root: Path | None = None) -> dict[str, Any] | None:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    return _safe_read_json(
        spx_root / "output/forecasts/latest_gap_augmented_range_skew_forecast.json"
    )


def load_daily_comparison_scorecard(spx_root: Path | None = None) -> pd.DataFrame:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    return _safe_read_csv(
        spx_root
        / "output/reports/daily_forecast_comparison/daily_hybrid_vs_range_skew_scorecard.csv"
    )


def load_daily_comparison_report(spx_root: Path | None = None, date_str: str = "") -> dict[str, Any] | None:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    if not date_str:
        return None
    return _safe_read_json(
        spx_root
        / "output/reports/daily_forecast_comparison"
        / f"{date_str}_hybrid_vs_range_skew_actuals.json"
    )


def load_forecast_archive(spx_root: Path | None = None) -> list[Path]:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    archive_dir = spx_root / "output/forecasts/archive"
    if not archive_dir.exists():
        return []
    return sorted(archive_dir.glob("*.json"), reverse=True)


def load_archived_forecast_by_name(spx_root: Path | None = None, filename: str = "") -> dict[str, Any] | None:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    if not filename:
        return None
    return _safe_read_json(spx_root / "output/forecasts/archive" / filename)


def latest_forecast_status(spx_root: Path | None = None) -> dict[str, Any]:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    hybrid = load_latest_hybrid_forecast(spx_root)
    rs = load_latest_range_skew_forecast(spx_root)

    hybrid_date = hybrid.get("forecast_for_date") if hybrid else None
    rs_date = rs.get("forecast_for_date") if rs else None

    status = "Missing Files"
    if hybrid and rs:
        if hybrid_date == rs_date:
            report = load_daily_comparison_report(spx_root, hybrid_date) if hybrid_date else None
            status = "Compared" if report else "Awaiting Actuals"
        else:
            status = "Forecast Date Mismatch"
    elif hybrid or rs:
        status = "Partial Forecast Set"

    return {
        "status": status,
        "hybrid_date": hybrid_date,
        "range_skew_date": rs_date,
        "hybrid_mtime": _mtime(
            spx_root / "output/forecasts/latest_gap_augmented_hybrid_ohlc_forecast.json"
        ),
        "range_skew_mtime": _mtime(
            spx_root / "output/forecasts/latest_gap_augmented_range_skew_forecast.json"
        ),
        "scorecard_mtime": _mtime(
            spx_root
            / "output/reports/daily_forecast_comparison/daily_hybrid_vs_range_skew_scorecard.csv"
        ),
    }


def list_comparison_report_dates(spx_root: Path | None = None) -> list[str]:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    report_dir = spx_root / "output/reports/daily_forecast_comparison"
    if not report_dir.exists():
        return []
    out: list[str] = []
    for p in sorted(report_dir.glob("*_hybrid_vs_range_skew_actuals.json"), reverse=True):
        name = p.name.replace("_hybrid_vs_range_skew_actuals.json", "")
        out.append(name)
    return out


def file_freshness(spx_root: Path | None = None) -> pd.DataFrame:
    spx_root = spx_root or DEFAULT_SPX_ROOT
    files = {
        "latest_hybrid_forecast": spx_root
        / "output/forecasts/latest_gap_augmented_hybrid_ohlc_forecast.json",
        "latest_range_skew_forecast": spx_root
        / "output/forecasts/latest_gap_augmented_range_skew_forecast.json",
        "comparison_scorecard": spx_root
        / "output/reports/daily_forecast_comparison/daily_hybrid_vs_range_skew_scorecard.csv",
        "latest_signal": spx_root / "output/signals/latest_signal.json",
        "spx_daily": spx_root / "data/raw/spx_daily.parquet",
        "vix_daily": spx_root / "data/raw/vix_daily.parquet",
    }

    rows = []
    now = pd.Timestamp.now()

    for label, path in files.items():
        exists = path.exists()
        mtime = pd.Timestamp(path.stat().st_mtime, unit="s") if exists else pd.NaT
        age_hours = None
        if exists:
            age_hours = round((now - mtime).total_seconds() / 3600.0, 2)
        rows.append(
            {
                "name": label,
                "path": str(path),
                "exists": exists,
                "modified_at": None if pd.isna(mtime) else mtime.isoformat(),
                "age_hours": age_hours,
            }
        )

    return pd.DataFrame(rows)

def load_forecast_scorecard(spx_root: Path | None = None) -> pd.DataFrame:
    return load_daily_comparison_scorecard(spx_root)
