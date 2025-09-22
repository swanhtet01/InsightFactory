"""Utilities for persisting pipeline run history for dashboards and analytics."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import json

import pandas as pd

HISTORY_PATH = Path("reports/run_history.csv")


def _normalize_value(value: Any) -> Any:
    """Convert complex objects into plain Python types suitable for CSV storage."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        try:
            return value.item()  # type: ignore[return-value]
        except Exception:
            pass
    return json.dumps(value, ensure_ascii=False)


def _flatten(prefix: str, payload: Any, row: Dict[str, Any]) -> None:
    if payload is None:
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_prefix = f"{prefix}_{key}" if prefix else str(key)
            _flatten(next_prefix, value, row)
        return
    if isinstance(payload, list):
        if not payload:
            return
        if all(isinstance(item, (str, int, float, bool)) for item in payload):
            row[prefix] = ", ".join(str(item) for item in payload)
        else:
            row[prefix] = _normalize_value(payload)
        return
    row[prefix] = _normalize_value(payload)


def flatten_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a nested summary dictionary into a single-row record."""
    row: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    prefix_map = {
        "kpis": "kpi",
        "claim_metrics": "claim",
        "document_metrics": "document",
        "ai_research": "ai",
    }
    for key, value in summary.items():
        prefix = prefix_map.get(key, str(key))
        _flatten(prefix, value, row)
    return row


def record_run(summary: Dict[str, Any]) -> Path:
    """Append the latest pipeline run to the historical CSV."""
    if not summary:
        return HISTORY_PATH

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = flatten_summary(summary)
    new_row = pd.DataFrame([row])

    if HISTORY_PATH.exists():
        history = pd.read_csv(HISTORY_PATH)
        combined = pd.concat([history, new_row], ignore_index=True, sort=False)
    else:
        combined = new_row

    # Ensure timestamp remains the first column for readability
    ordered_columns = [col for col in combined.columns if col != "timestamp"]
    ordered_columns.sort()
    combined = combined[["timestamp", *ordered_columns]]
    combined.to_csv(HISTORY_PATH, index=False)
    return HISTORY_PATH
