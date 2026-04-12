from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from dashboard.config import OPTIONS_ALGO_V2_DB_PATH


def _connect() -> sqlite3.Connection | None:
    db_path = Path(OPTIONS_ALGO_V2_DB_PATH)
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_db_status() -> dict[str, object]:
    db_path = Path(OPTIONS_ALGO_V2_DB_PATH)
    return {
        "db_path": str(db_path),
        "exists": db_path.exists(),
        "size_bytes": db_path.stat().st_size if db_path.exists() else None,
    }


def get_latest_run_id() -> str | None:
    conn = _connect()
    if conn is None:
        return None
    try:
        row = conn.execute(
            "select run_id from scan_run_summary order by timestamp_utc desc limit 1"
        ).fetchone()
        return str(row["run_id"]) if row else None
    finally:
        conn.close()


def get_latest_run_summary() -> dict[str, object] | None:
    conn = _connect()
    if conn is None:
        return None
    try:
        row = conn.execute(
            "select * from scan_run_summary order by timestamp_utc desc limit 1"
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_latest_symbol_rows(limit: int = 200) -> pd.DataFrame:
    conn = _connect()
    if conn is None:
        return pd.DataFrame()

    try:
        run_id = get_latest_run_id()
        if not run_id:
            return pd.DataFrame()

        query = """
        select
            run_id,
            timestamp_utc,
            symbol,
            final_passed,
            final_score,
            min_score_required,
            market_regime,
            directional_state,
            iv_state,
            signal_state,
            strategy_type,
            options_context_pre_context_score,
            options_context_pre_context_score_gap,
            options_context_borderline_score_pass,
            options_context_borderline_score_pass_tier_a,
            options_context_borderline_score_pass_tier_b,
            options_context_borderline_rescue_tier,
            options_context_effective_soft_penalties_json,
            blocking_reasons_json,
            soft_penalty_reasons_json
        from scan_symbol_decisions
        where run_id = ?
        order by final_passed desc, final_score desc, symbol asc
        limit ?
        """
        df = pd.read_sql_query(query, conn, params=[run_id, limit])
        return df
    finally:
        conn.close()


def get_recent_symbol_history(symbols: list[str], limit_runs: int = 20) -> pd.DataFrame:
    if not symbols:
        return pd.DataFrame()

    conn = _connect()
    if conn is None:
        return pd.DataFrame()

    try:
        run_rows = conn.execute(
            """
            select run_id
            from scan_run_summary
            order by timestamp_utc desc
            limit ?
            """,
            [limit_runs],
        ).fetchall()
        run_ids = [str(r["run_id"]) for r in run_rows]
        if not run_ids:
            return pd.DataFrame()

        placeholders_runs = ",".join("?" for _ in run_ids)
        placeholders_symbols = ",".join("?" for _ in symbols)

        query = f"""
        select
            run_id,
            timestamp_utc,
            symbol,
            final_passed,
            final_score,
            min_score_required,
            options_context_pre_context_score,
            options_context_pre_context_score_gap,
            options_context_borderline_rescue_tier,
            options_context_effective_soft_penalties_json
        from scan_symbol_decisions
        where run_id in ({placeholders_runs})
          and symbol in ({placeholders_symbols})
        order by timestamp_utc desc, symbol asc
        """

        params = run_ids + [s.upper() for s in symbols]
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def get_rescue_summary(limit_runs: int = 20) -> dict[str, object]:
    conn = _connect()
    if conn is None:
        return {
            "tier_a_count": 0,
            "tier_b_count": 0,
            "rescued_pass_count": 0,
            "normal_pass_count": 0,
            "top_tier_a_symbols": [],
            "top_tier_b_symbols": [],
        }

    try:
        run_rows = conn.execute(
            """
            select run_id
            from scan_run_summary
            order by timestamp_utc desc
            limit ?
            """,
            [limit_runs],
        ).fetchall()
        run_ids = [str(r["run_id"]) for r in run_rows]
        if not run_ids:
            return {
                "tier_a_count": 0,
                "tier_b_count": 0,
                "rescued_pass_count": 0,
                "normal_pass_count": 0,
                "top_tier_a_symbols": [],
                "top_tier_b_symbols": [],
            }

        placeholders = ",".join("?" for _ in run_ids)

        base_query = f"""
        from scan_symbol_decisions
        where run_id in ({placeholders})
        """

        tier_a_count = conn.execute(
            f"""
            select count(*)
            {base_query}
              and options_context_borderline_score_pass_tier_a = 1
            """,
            run_ids,
        ).fetchone()[0]

        tier_b_count = conn.execute(
            f"""
            select count(*)
            {base_query}
              and options_context_borderline_score_pass_tier_b = 1
            """,
            run_ids,
        ).fetchone()[0]

        rescued_pass_count = conn.execute(
            f"""
            select count(*)
            {base_query}
              and final_passed = 1
              and options_context_borderline_score_pass = 1
            """,
            run_ids,
        ).fetchone()[0]

        normal_pass_count = conn.execute(
            f"""
            select count(*)
            {base_query}
              and final_passed = 1
              and coalesce(options_context_borderline_score_pass, 0) = 0
            """,
            run_ids,
        ).fetchone()[0]

        tier_a_rows = conn.execute(
            f"""
            select symbol, count(*) as n
            {base_query}
              and options_context_borderline_score_pass_tier_a = 1
            group by symbol
            order by n desc, symbol asc
            limit 10
            """,
            run_ids,
        ).fetchall()

        tier_b_rows = conn.execute(
            f"""
            select symbol, count(*) as n
            {base_query}
              and options_context_borderline_score_pass_tier_b = 1
            group by symbol
            order by n desc, symbol asc
            limit 10
            """,
            run_ids,
        ).fetchall()

        return {
            "tier_a_count": int(tier_a_count or 0),
            "tier_b_count": int(tier_b_count or 0),
            "rescued_pass_count": int(rescued_pass_count or 0),
            "normal_pass_count": int(normal_pass_count or 0),
            "top_tier_a_symbols": [dict(r) for r in tier_a_rows],
            "top_tier_b_symbols": [dict(r) for r in tier_b_rows],
        }
    finally:
        conn.close()


def get_overlap_anomaly_count() -> int:
    conn = _connect()
    if conn is None:
        return 0
    try:
        row = conn.execute(
            """
            select count(*) as n
            from scan_symbol_decisions
            where options_context_borderline_score_pass_tier_a = 1
              and options_context_borderline_score_pass_tier_b = 1
            """
        ).fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()


def decode_jsonish_column(series: pd.Series) -> pd.Series:
    def _decode(value):
        if value in (None, "", "null"):
            return []
        if isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except Exception:
            return [str(value)]
    return series.apply(_decode)
