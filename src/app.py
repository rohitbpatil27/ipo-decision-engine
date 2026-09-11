from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import os
from pathlib import Path

from src.config import FRONTEND_DIR, IS_VERCEL, BASE_DIR
from src.storage import Storage
from src.scraper import IPOScraper
from src.scheduler import BackgroundScheduler
from src.models import IPODetail

app = FastAPI(
    title="IPO Decision Engine API",
    description="Automated valuation and decision engine for Indian Mainboard IPOs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = Storage()
scraper = IPOScraper(storage)
scheduler = BackgroundScheduler(scraper)

# Only start continuous background scheduler thread in dedicated server mode (not in Vercel serverless)
if not IS_VERCEL:
    @app.on_event("startup")
    def startup_event():
        scheduler.start()

    @app.on_event("shutdown")
    def shutdown_event():
        scheduler.stop()

from fastapi.responses import HTMLResponse

def _get_index_content() -> str:
    candidates = [
        FRONTEND_DIR / "index.html",
        BASE_DIR / "index.html",
        Path("index.html"),
        Path("frontend/index.html")
    ]
    for candidate in candidates:
        try:
            if candidate.exists():
                with open(candidate, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception:
            pass
    return "<h1>IPO Advisor</h1><p>Frontend loading...</p>"

@app.get("/api")
@app.get("/api/")
def api_root():
    return {
        "app": "IPO Decision Engine API",
        "status": "online",
        "version": "1.0.0",
        "environment": "vercel-serverless" if IS_VERCEL else "standalone"
    }

@app.get("/api/ipos", response_model=List[IPODetail])
@app.get("/ipos", response_model=List[IPODetail])
def list_ipos(
    status: Optional[str] = Query(None, description="Filter by status: open, upcoming, or all"),
    sort: Optional[str] = Query("date", description="Sort by: date, priority, sub, gmp_desc, score_desc")
):
    """
    Returns list of Mainboard IPOs with calculated verdicts.
    Strictly excludes SME IPOs.
    Defaults to sorting by Date (closing soonest for Open, opening soonest for Upcoming).
    """
    status_filter = None
    if status and status.lower() in ["open", "upcoming"]:
        status_filter = status.upper()

    ipos = storage.get_all_ipos(status_filter=status_filter)

    # Sorting
    if sort == "priority":
        ipos.sort(key=lambda x: (x.priority_rank or 999))
    elif sort == "sub":
        ipos.sort(key=lambda x: (x.hype.subscription_times or -1), reverse=True)
    elif sort in ["gmp_desc", "gmp"]:
        ipos.sort(key=lambda x: (x.hype.gmp_pct or -999), reverse=True)
    elif sort in ["score_desc", "score"]:
        ipos.sort(key=lambda x: (x.fundamentals.total_score or 0), reverse=True)
    else:
        # Default: Sort strictly by Date
        # For open IPOs, close_date ascending (urgent closes first), secondary by priority rank
        # For upcoming IPOs, open_date ascending (upcoming opens first)
        def date_sort_key(item: IPODetail):
            # Prioritize open items first if viewing mixed/all
            status_order = 0 if item.status.value == "OPEN" else (1 if item.status.value == "UPCOMING" else 2)
            if item.status.value == "OPEN":
                target_date = item.close_date if (item.close_date and item.close_date != "TBD") else "9999-99-99"
            else:
                target_date = item.open_date if (item.open_date and item.open_date != "TBD") else "9999-99-99"
            p_rank = item.priority_rank or 999
            return (status_order, target_date, p_rank)

        ipos.sort(key=date_sort_key)

    return ipos

@app.get("/api/ipos/{ipo_id}", response_model=IPODetail)
@app.get("/ipos/{ipo_id}", response_model=IPODetail)
def get_ipo_detail(ipo_id: int):
    """
    Returns detailed IPO record including 3-year DRHP financials,
    sub-scores, and comprehensive strategic verdict rationale.
    """
    ipo = storage.get_ipo_by_id(ipo_id)
    if not ipo:
        raise HTTPException(status_code=404, detail="IPO not found")
    return ipo

@app.post("/api/refresh")
@app.post("/refresh")
def trigger_refresh(background_tasks: BackgroundTasks):
    """
    Triggers an immediate live scraping and re-calculation cycle online.
    """
    if scheduler.is_syncing:
        return {"status": "in_progress", "message": "Synchronization is already running."}
    
    background_tasks.add_task(scheduler._do_sync)
    return {"status": "started", "message": "Live IPO data refresh initiated."}

@app.get("/api/status")
@app.get("/status")
def get_system_status():
    """
    Returns status of data synchronization, last updated timestamp,
    and count of active Mainboard IPOs.
    """
    stats = storage.get_stats()
    return {
        "status": "online",
        "is_syncing": scheduler.is_syncing,
        "last_updated": scheduler.last_run_time or stats.get("last_updated"),
        "next_scheduled_run": scheduler.next_run_time,
        "stats": stats
    }

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
def serve_index():
    """Serves the Zerodha-style IPO dashboard frontend"""
    return HTMLResponse(content=_get_index_content())

# Mount static frontend directory if available
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

# Catch-all GET route for Single Page Application routing (avoids 404s on Vercel rewrites)
@app.get("/{full_path:path}", response_class=HTMLResponse)
def catch_all(full_path: str):
    return HTMLResponse(content=_get_index_content())
