import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["VERCEL"] = "1"

from fastapi import FastAPI, BackgroundTasks
from src.app import trigger_refresh

app = FastAPI(title="IPO Decision Engine - Refresh")

@app.post("/api/refresh")
@app.post("/refresh")
@app.post("/")
@app.get("/api/refresh")
@app.get("/refresh")
@app.get("/")
def refresh_endpoint(background_tasks: BackgroundTasks):
    return trigger_refresh(background_tasks)

__all__ = ["app"]
