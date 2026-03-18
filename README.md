# Trading Dashboard

Shared Streamlit dashboard for **SPX Algo** and **Options Algo** monitoring.

This dashboard provides a single UI for:
- SPX forecast monitoring
- SPX comparison history
- SPX archive inspection
- Options overview / paper-live visibility
- shared health and freshness checks across both systems

## Features

### SPX pages
- **Home** — top-level system summary
- **SPX Daily Monitor** — latest predicted vs actual view
- **SPX Forecasts** — latest forecast payload details
- **SPX Comparison History** — scorecard and model tracking
- **SPX Actual vs Predicted** — actual vs forecast inspection
- **SPX Archive Browser** — archived forecast browsing
- **Ops / Freshness** — SPX artifact freshness checks

### Shared / cross-system pages
- **Shared Health Check** — unified health and freshness checks for SPX Algo + Options Algo

### Options pages
- **Options Overview** — latest options scan / paper-live monitoring

---

## Repo structure

```text
trading_dashboard/
├── app.py
├── requirements.txt
├── dashboard/
│   ├── config.py
│   ├── components/
│   ├── loaders/
│   └── pages/
└── README.md
Copy
Key files
app.py — Streamlit entrypoint and sidebar navigation
dashboard/config.py — app title, icon, SPX root, options roots
dashboard/loaders/ — data loaders for SPX, options, and health checks
dashboard/pages/ — page renderers
Requirements
Install Python dependencies:

Copypip install -r requirements.txt
Current requirements:

streamlit>=1.32
pandas>=2.2
plotly>=5.19
pyarrow>=14.0
streamlit-autorefresh>=1.0.1
Configuration
The dashboard reads configuration from environment variables in dashboard/config.py.

Supported environment variables
CopyAPP_TITLE
APP_ICON
SPX_ALGO_ROOT
OPTIONS_ALGO_ROOT
OPTIONS_ALGO_V2_ROOT
OPTIONS_ALGO_V2_DATA_ROOT
Defaults
If not set, the app uses:

CopyAPP_TITLE="Trading Dashboard"
APP_ICON="📊"

SPX_ALGO_ROOT=/root/spx_algo
OPTIONS_ALGO_ROOT=/root/options_algo
OPTIONS_ALGO_V2_ROOT=/root/options_algo_v2
OPTIONS_ALGO_V2_DATA_ROOT=/root/options_algo_v2/data
Example .env
CopyAPP_TITLE="Trading Dashboard"
APP_ICON="📊"
SPX_ALGO_ROOT="/root/spx_algo"
OPTIONS_ALGO_ROOT="/root/options_algo"
OPTIONS_ALGO_V2_ROOT="/root/options_algo_v2"
OPTIONS_ALGO_V2_DATA_ROOT="/root/options_algo_v2/data"
Running locally
From the repo root:

Copycd /root/trading_dashboard
streamlit run app.py --server.port 8503 --server.address 0.0.0.0
Then open:

Copyhttp://localhost:8503
or from another machine:

Copyhttp://<server-ip>:8503
Production service
This dashboard is typically run via systemd.

Restart
Copysystemctl restart trading-dashboard
Status
Copysystemctl status trading-dashboard --no-pager
Logs
Copyjournalctl -u trading-dashboard -n 100 --no-pager
Auto-refresh
The dashboard auto-refreshes every 5 minutes using:

streamlit_autorefresh
Configured in app.py:

Copyst_autorefresh(interval=300000, key="dashboard_refresh")
Data sources
SPX Algo
The dashboard reads from the SPX repo root, usually:

Copy/root/spx_algo
Typical artifacts used:

output/signals/latest_signal.json
output/forecasts/latest_gap_augmented_hybrid_ohlc_forecast.json
output/forecasts/latest_gap_augmented_range_skew_forecast.json
output/reports/daily_forecast_comparison/daily_hybrid_vs_range_skew_scorecard.csv
processed parquet feature/data files under data/processed/
raw parquet market files under data/raw/
Options Algo
The dashboard reads from the legacy Options root and/or Options V2 root, depending on the page.

Current health-check artifacts include:

/root/options_algo/output/signals/options_signal_latest.json
/root/options_algo/output/trades/trade_outcomes.jsonl
Options overview data may additionally depend on:

OPTIONS_ALGO_V2_ROOT
OPTIONS_ALGO_V2_DATA_ROOT
Shared Health Check page
The Shared Health Check tab provides a unified status view for:

SPX artifact freshness
Options artifact freshness
latest signal / forecast dates
file mtimes and sizes
processed parquet max dates
This is intended as a quick operational page to confirm:

forecasts are current
signals are current
comparison scorecard is updating
upstream artifacts are not stale
Sidebar navigation
The app uses a manual sidebar navigation defined in app.py.

Current pages:

🏠 Home
📈 SPX Daily Monitor
📉 SPX Forecasts
📊 SPX Comparison History
🎯 SPX Actual vs Predicted
🗂️ SPX Archive Browser
🧾 Options Overview
🩺 Shared Health Check
🛠️ Ops / Freshness
Development notes
Adding a new page
Create a new module under:
Copydashboard/pages/
Import it in app.py

Add it to the sidebar radio list

Add a matching render branch

Adding a new loader
Create a module under:

Copydashboard/loaders/
and import it from the relevant page.

Quick commands
Syntax check
Copypython3.11 -m py_compile app.py
find dashboard -name "*.py" -print0 | xargs -0 -n1 python3.11 -m py_compile
Run dashboard
Copycd /root/trading_dashboard
streamlit run app.py --server.port 8503 --server.address 0.0.0.0
Restart production service
Copysystemctl restart trading-dashboard
journalctl -u trading-dashboard -n 50 --no-pager
Git commit
Copycd /root/trading_dashboard
git add README.md
git commit -m "Update README with dashboard setup and health check page"
git push origin main
Notes
The dashboard is a read-only monitoring UI over SPX and Options artifacts.
If a page shows stale data, first verify the upstream algo outputs and cron jobs.
Streamlit deprecation warnings related to use_container_width may still appear until remaining page components are updated to width="stretch" / width="content".
MD


---

# 2) Optional quick review
```bash
sed -n '1,260p' /root/trading_dashboard/README.md
3) Commit and push
Copycd /root/trading_dashboard
git add README.md
git commit -m "Update README with dashboard setup and health check details"
git push origin main
4) Verify
Copygit log -1 --stat
git status
