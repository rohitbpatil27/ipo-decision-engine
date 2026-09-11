import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["VERCEL"] = "1"

from fastapi import FastAPI
from src.app import get_system_status

app = FastAPI(title="IPO Decision Engine - Status")

@app.get("/api/status")
@app.get("/status")
@app.get("/")
def status_endpoint():
    return get_system_status()

__all__ = ["app"]
