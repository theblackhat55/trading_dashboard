from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from dashboard.config import OPTIONS_ALGO_V2_DATA_ROOT, OPTIONS_ROOT


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def _safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def get_options_algo_v2_data_root() -> Path:
    return OPTIONS_ALGO_V2_DATA_ROOT


def get_scan_results_dir() -> Path:
    return get_options_algo_v2_data_root() / "scan_results"


def get_validation_dir() -> Path:
    return get_options_algo_v2_data_root() / "validation"


def get_state_dir() -> Path:
    return get_options_algo_v2_data_root() / "state"


def list_scan_files(limit: int = 100) -> list[Path]:
    files = sorted(get_scan_results_dir().glob("scan_*.json"))
    if limit <= 0:
        return files
    return files[-limit:]


def load_latest_scan() -> dict[str, Any] | None:
    files = list_scan_files(limit=1)
    if not files:
        return None
    payload = _read_json(files[-1])
    return payload if isinstance(payload, dict) else None


def load_recent_scans(limit: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in reversed(list_scan_files(limit=limit)):
        payload = _read_json(path)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def load_paper_live_runs() -> pd.DataFrame:
    return _read_jsonl(get_validation_dir() / "paper_live_runs.jsonl")


def load_paper_live_symbol_decisions() -> pd.DataFrame:
    return _read_jsonl(get_validation_dir() / "paper_live_symbol_decisions.jsonl")


def load_iv_proxy_history() -> pd.DataFrame:
    return _read_jsonl(get_state_dir() / "iv_proxy_history.jsonl")


def build_latest_scan_summary() -> dict[str, Any]:
    payload = load_latest_scan()
    if not payload:
        return {}

    summary = _safe_dict(payload.get("summary"))
    runtime_metadata = _safe_dict(payload.get("runtime_metadata"))

    return {
        "run_id": payload.get("run_id"),
        "generated_at": payload.get("generated_at"),
        "runtime_mode": runtime_metadata.get("runtime_mode"),
        "as_of_date": runtime_metadata.get("as_of_date"),
        "strict_live_mode": runtime_metadata.get("strict_live_mode"),
        "degraded_live_mode": runtime_metadata.get("degraded_live_mode"),
        "total_candidates": summary.get("total_candidates", 0),
        "total_passed": summary.get("total_passed", 0),
        "total_rejected": summary.get("total_rejected", 0),
        "trade_idea_count": runtime_metadata.get("trade_idea_count", 0),
        "top_trade_candidate_symbols": runtime_metadata.get(
            "top_trade_candidate_symbols",
            [],
        ),
        "trade_idea_symbols": runtime_metadata.get("trade_idea_symbols", []),
        "used_placeholder_iv_inputs": runtime_metadata.get(
            "used_placeholder_iv_inputs",
            False,
        ),
        "used_placeholder_iv_rank_inputs": runtime_metadata.get(
            "used_placeholder_iv_rank_inputs",
            False,
        ),
        "used_placeholder_iv_hv_ratio_inputs": runtime_metadata.get(
            "used_placeholder_iv_hv_ratio_inputs",
            False,
        ),
        "used_placeholder_liquidity_inputs": runtime_metadata.get(
            "used_placeholder_liquidity_inputs",
            False,
        ),
        "iv_rank_ready_symbols": runtime_metadata.get("iv_rank_ready_symbols", []),
        "iv_rank_insufficient_history_symbols": runtime_metadata.get(
            "iv_rank_insufficient_history_symbols",
            [],
        ),
        "iv_rank_observation_count_by_symbol": runtime_metadata.get(
            "iv_rank_observation_count_by_symbol",
            {},
        ),
        "aggregate_quote_quality_counts": runtime_metadata.get(
            "aggregate_quote_quality_counts",
            {},
        ),
        "rejection_reason_counts": summary.get("rejection_reason_counts", {}),
        "signal_state_counts": summary.get("signal_state_counts", {}),
        "strategy_type_counts": summary.get("strategy_type_counts", {}),
    }


def build_latest_trade_candidates_df() -> pd.DataFrame:
    payload = load_latest_scan()
    if not payload:
        return pd.DataFrame()

    candidates = payload.get("trade_candidates", [])
    if not isinstance(candidates, list):
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "symbol": item.get("symbol"),
                "strategy_family": item.get("strategy_family"),
                "expiration": item.get("expiration"),
                "net_credit": item.get("net_credit"),
                "net_debit": item.get("net_debit"),
                "width": item.get("width"),
                "score": item.get("score"),
            }
        )
    return pd.DataFrame(rows)


def build_latest_trade_ideas_df() -> pd.DataFrame:
    payload = load_latest_scan()
    if not payload:
        return pd.DataFrame()

    ideas = payload.get("trade_ideas", [])
    if not isinstance(ideas, list):
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for item in ideas:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "symbol": item.get("symbol"),
                "strategy_family": item.get("strategy_family"),
                "expiration": item.get("expiration"),
                "net_credit": item.get("net_credit"),
                "net_debit": item.get("net_debit"),
                "width": item.get("width"),
                "max_risk": item.get("max_risk"),
                "score": item.get("score"),
            }
        )
    return pd.DataFrame(rows)


def build_recent_paper_live_summary() -> dict[str, Any]:
    runs = load_paper_live_runs()
    if runs.empty:
        return {}

    result: dict[str, Any] = {
        "run_count": int(len(runs)),
        "average_pass_rate": None,
        "degraded_live_mode_count": 0,
        "used_placeholder_iv_rank_inputs_count": 0,
        "used_placeholder_iv_hv_ratio_inputs_count": 0,
    }

    if {"passed_count", "symbol_count"}.issubset(runs.columns):
        denom = runs["symbol_count"].replace(0, pd.NA)
        pass_rate = (runs["passed_count"] / denom).dropna()
        if not pass_rate.empty:
            result["average_pass_rate"] = float(pass_rate.mean())

    for col in [
        "degraded_live_mode",
        "used_placeholder_iv_rank_inputs",
        "used_placeholder_iv_hv_ratio_inputs",
    ]:
        if col in runs.columns:
            result[f"{col}_count"] = int(runs[col].fillna(False).astype(bool).sum())

    return result


def build_symbol_leaderboard_df() -> pd.DataFrame:
    df = load_paper_live_symbol_decisions()
    if df.empty or "symbol" not in df.columns:
        return pd.DataFrame()

    working = df.copy()

    if "final_passed" in working.columns:
        working["final_passed"] = working["final_passed"].fillna(False).astype(bool)
    else:
        working["final_passed"] = False

    grouped = working.groupby("symbol", dropna=False)

    rows: list[dict[str, Any]] = []
    for symbol, group in grouped:
        seen = int(len(group))
        passes = int(group["final_passed"].sum())
        pass_rate = (passes / seen) if seen > 0 else 0.0

        avg_score = (
            float(group["final_score"].dropna().mean())
            if "final_score" in group.columns and not group["final_score"].dropna().empty
            else None
        )
        avg_adx14 = (
            float(group["adx14"].dropna().mean())
            if "adx14" in group.columns and not group["adx14"].dropna().empty
            else None
        )
        avg_iv_hv_ratio = (
            float(group["iv_hv_ratio"].dropna().mean())
            if "iv_hv_ratio" in group.columns and not group["iv_hv_ratio"].dropna().empty
            else None
        )

        top_directional_state = None
        if "directional_state" in group.columns:
            vc = group["directional_state"].dropna().astype(str).value_counts()
            if not vc.empty:
                top_directional_state = str(vc.index[0])

        top_rejection_reason = None
        if "rejection_reasons" in group.columns:
            exploded = (
                group["rejection_reasons"]
                .dropna()
                .astype(str)
                .value_counts()
            )
            if not exploded.empty:
                top_rejection_reason = str(exploded.index[0])

        rows.append(
            {
                "symbol": symbol,
                "seen": seen,
                "passes": passes,
                "pass_rate": pass_rate,
                "avg_score": avg_score,
                "avg_adx14": avg_adx14,
                "avg_iv_hv_ratio": avg_iv_hv_ratio,
                "top_directional_state": top_directional_state,
                "top_rejection_reason": top_rejection_reason,
            }
        )

    leaderboard = pd.DataFrame(rows)
    if leaderboard.empty:
        return leaderboard
    return leaderboard.sort_values(
        by=["pass_rate", "passes", "seen"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def build_iv_rank_readiness_summary() -> dict[str, Any]:
    latest = build_latest_scan_summary()
    iv_history = load_iv_proxy_history()

    counts_by_symbol: dict[str, int] = {}
    if not iv_history.empty and "symbol" in iv_history.columns:
        vc = iv_history["symbol"].astype(str).value_counts()
        counts_by_symbol = {str(k): int(v) for k, v in vc.to_dict().items()}

    return {
        "ready_symbols": latest.get("iv_rank_ready_symbols", []),
        "insufficient_history_symbols": latest.get(
            "iv_rank_insufficient_history_symbols",
            [],
        ),
        "observation_count_by_symbol": latest.get(
            "iv_rank_observation_count_by_symbol",
            counts_by_symbol,
        ),
        "iv_history_rows": int(len(iv_history)) if not iv_history.empty else 0,
    }


# Legacy readers retained for backward compatibility
def load_latest_options_signal() -> dict[str, Any] | None:
    candidates = [
        OPTIONS_ROOT / "output" / "signals" / "options_signal_latest.json",
        OPTIONS_ROOT / "output" / "signals" / "latest_signal.json",
    ]
    for p in candidates:
        x = _read_json(p)
        if isinstance(x, dict):
            return x
    return None


def load_positions() -> dict[str, Any] | list[Any] | None:
    return _read_json(OPTIONS_ROOT / "output" / "trades" / "positions.json")


def load_trade_outcomes() -> pd.DataFrame:
    return _read_jsonl(OPTIONS_ROOT / "output" / "trades" / "trade_outcomes.jsonl")


# Backward-compatible alias
def load_latest_signal() -> dict[str, Any] | None:
    return load_latest_options_signal()
