from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_TITLE = os.getenv("APP_TITLE", "Trading Dashboard")
APP_ICON = os.getenv("APP_ICON", "📊")

SPX_ALGO_ROOT = Path(os.getenv("SPX_ALGO_ROOT", "/root/spx_algo"))
OPTIONS_ALGO_ROOT = Path(os.getenv("OPTIONS_ALGO_ROOT", "/root/options_algo"))

# Backward-compatible aliases for older dashboard modules
SPX_ROOT = SPX_ALGO_ROOT
OPTIONS_ROOT = OPTIONS_ALGO_ROOT
