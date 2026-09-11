import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Detect Vercel serverless environment (read-only filesystem except /tmp)
IS_VERCEL = bool(os.environ.get("VERCEL"))

if IS_VERCEL:
    DATA_DIR = Path("/tmp")
    DB_PATH = DATA_DIR / "ipo_advisor.db"
    
    # Seed /tmp/ipo_advisor.db from bundled data/ipo_advisor.db on cold start
    bundled_db = BASE_DIR / "data" / "ipo_advisor.db"
    if not DB_PATH.exists() and bundled_db.exists():
        try:
            shutil.copy2(bundled_db, DB_PATH)
        except Exception as e:
            print(f"Warning: Could not seed /tmp DB: {e}")
else:
    DATA_DIR = BASE_DIR / "data"
    try:
        DATA_DIR.mkdir(exist_ok=True)
    except Exception:
        pass
    DB_PATH = DATA_DIR / "ipo_advisor.db"

FRONTEND_DIR = BASE_DIR / "frontend"

# Scraper Endpoints & Headers
INVESTORGAIN_API_URL = "https://webnodejs.investorgain.com/cloud/v2/report/data-read/331/1/9/2026/2026-27/0/all?search=&v=00-03"
CHITTORGARH_BASE_URL = "https://www.chittorgarh.com"

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.investorgain.com/"
}

# Decision Engine Thresholds
FUNDAMENTAL_STRONG_THRESHOLD = 60.0    # Score >= 60 indicates solid fundamental base
GMP_HIGH_THRESHOLD = 20.0             # GMP% >= 20% indicates strong listing gain sentiment
GMP_VERY_HIGH_THRESHOLD = 25.0        # GMP% >= 25% allows listing-gain-only even with weaker fundamentals
GMP_WEAK_THRESHOLD = 15.0             # GMP% < 15% offers insufficient listing buffer for weak fundamentals

# Return and Leverage Ratios
IDEAL_ROE = 15.0                      # ROE >= 15% is healthy
IDEAL_ROCE = 15.0                     # ROCE >= 15% is healthy
IDEAL_DEBT_TO_EQUITY = 1.0            # D/E <= 1.0 is healthy, > 1.5 is risky
IDEAL_PE_BENCHMARK = 35.0             # Fair P/E reference point for broad market offerings

# Update Settings
AUTO_UPDATE_INTERVAL_HOURS = 24       # Daily auto-refresh frequency
