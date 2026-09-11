import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["VERCEL"] = "1"

from fastapi import FastAPI, Query
from typing import Optional, List
from src.models import IPODetail
from src.app import list_ipos

app = FastAPI(title="IPO Decision Engine - List IPOs")

@app.get("/api/ipos", response_model=List[IPODetail])
@app.get("/ipos", response_model=List[IPODetail])
@app.get("/", response_model=List[IPODetail])
def get_ipos(
    status: Optional[str] = Query(None, description="Filter by status: open, upcoming, or all"),
    sort: Optional[str] = Query("date", description="Sort by: date, priority, sub, gmp_desc, score_desc")
):
    return list_ipos(status=status, sort=sort)

__all__ = ["app"]
