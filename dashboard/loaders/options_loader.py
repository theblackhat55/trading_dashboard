from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from dashboard.config import OPTIONS_ROOT


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
    rows = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


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
