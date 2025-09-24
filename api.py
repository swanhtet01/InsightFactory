"""FastAPI gateway exposing InsightFactory analytics artifacts."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from config import (
    API_ALLOWED_ORIGINS,
    INSIGHT_API_KEY,
    INSIGHT_API_KEY_HEADER,
    REPORTS_DIR,
)

SUMMARY_FILENAME = "latest_summary.json"
HISTORY_FILENAME = "run_history.csv"
HTML_FILENAME = "latest_summary.html"


def _ensure_reports_dir() -> Path:
    """Return the reports directory ensuring it exists."""

    reports_dir = REPORTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def _load_summary() -> dict[str, Any]:
    reports_dir = _ensure_reports_dir()
    path = reports_dir / SUMMARY_FILENAME
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Pipeline summary not found. Execute the pipeline to generate reports.",
        )
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_run_history(limit: Optional[int] = None) -> list[dict[str, Any]]:
    reports_dir = _ensure_reports_dir()
    path = reports_dir / HISTORY_FILENAME
    if not path.exists():
        return []
    history = pd.read_csv(path)
    if "timestamp" in history.columns:
        history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
        history = history.sort_values("timestamp")
    if limit:
        history = history.tail(limit)
    return history.fillna("").to_dict(orient="records")


def _load_html_report() -> str:
    reports_dir = _ensure_reports_dir()
    path = reports_dir / HTML_FILENAME
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="HTML summary not found. Execute the pipeline to generate reports.",
        )
    return path.read_text(encoding="utf-8")


API_KEY_HEADER = APIKeyHeader(name=INSIGHT_API_KEY_HEADER, auto_error=False)


def get_api_key(api_key_header: Optional[str] = Security(API_KEY_HEADER)) -> str:
    expected_key = INSIGHT_API_KEY
    if not expected_key:
        raise HTTPException(status_code=500, detail="INSIGHT_API_KEY is not configured")
    if api_key_header == expected_key:
        return expected_key
    raise HTTPException(status_code=403, detail="Invalid API key")


app = FastAPI(
    title="InsightFactory API",
    description="Read-only access to KPI, claim, and document analytics artifacts.",
    version="2.0.0",
    openapi_tags=[
        {"name": "health", "description": "Service availability"},
        {"name": "analytics", "description": "Pipeline outputs for ERP dashboards"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=API_ALLOWED_ORIGINS if API_ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def root() -> dict[str, Any]:
    return {
        "status": "ok",
        "message": "InsightFactory API is running.",
        "endpoints": [
            "/api/health",
            "/api/summary",
            "/api/run-history",
            "/api/insights",
            "/api/report/html",
        ],
    }


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    reports_dir = _ensure_reports_dir()
    latest_summary = reports_dir / SUMMARY_FILENAME
    latest_history = reports_dir / HISTORY_FILENAME
    return {
        "status": "ok",
        "summary_available": str(latest_summary.exists()).lower(),
        "run_history_available": str(latest_history.exists()).lower(),
    }


@app.get("/api/summary", tags=["analytics"])
def get_summary(_: str = Depends(get_api_key)) -> dict[str, Any]:
    return _load_summary()


@app.get("/api/run-history", tags=["analytics"])
def get_run_history(
    limit: Optional[int] = Query(None, ge=1, description="Number of most recent runs to return"),
    _: str = Depends(get_api_key),
) -> dict[str, Any]:
    records = _load_run_history(limit)
    return {"records": records, "count": len(records)}


@app.get("/api/insights", tags=["analytics"])
def get_insights(_: str = Depends(get_api_key)) -> dict[str, Any]:
    summary = _load_summary()
    return {
        "ai_research": summary.get("ai_research", {}),
        "performance_insights": summary.get("performance_insights", {}),
        "autonomy_plan": summary.get("autonomy_plan", {}),
        "run_metadata": summary.get("run_metadata", {}),
    }


@app.get("/api/report/html", tags=["analytics"])
def get_html_report(_: str = Depends(get_api_key)) -> Response:
    html = _load_html_report()
    return Response(content=html, media_type="text/html")


if __name__ == "__main__":  # pragma: no cover - manual launch convenience
    import uvicorn

    uvicorn.run(
        "api:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
    )
