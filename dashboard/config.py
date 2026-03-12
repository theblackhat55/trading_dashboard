from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_TITLE = os.getenv("APP_TITLE", "Trading Dashboard")
APP_ICON = os.getenv("APP_ICON", "📊")

SPX_ALGO_ROOT = Path(os.getenv("SPX_ALGO_ROOT", "/root/spx_algo"))

LEGACY_OPTIONS_ALGO_ROOT = Path(os.getenv("OPTIONS_ALGO_ROOT", "/root/options_algo"))
OPTIONS_ALGO_V2_ROOT = Path(
    os.getenv("OPTIONS_ALGO_V2_ROOT", "/root/options_algo_v2")
)

_options_algo_v2_data_root_env = os.getenv("OPTIONS_ALGO_V2_DATA_ROOT")
if _options_algo_v2_data_root_env:
    OPTIONS_ALGO_V2_DATA_ROOT = Path(_options_algo_v2_data_root_env)
else:
    OPTIONS_ALGO_V2_DATA_ROOT = OPTIONS_ALGO_V2_ROOT / "data"

# Backward-compatible aliases for older dashboard modules
SPX_ROOT = SPX_ALGO_ROOT
OPTIONS_ROOT = LEGACY_OPTIONS_ALGO_ROOT
