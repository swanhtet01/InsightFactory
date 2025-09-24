"""Utilities for capturing and loading Drive sync metadata."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Any, Dict, Iterable, List


SNAPSHOT_PATH = Path("reports/latest_sources.json")


def slugify_label(label: str) -> str:
    """Convert a folder label into a filesystem-friendly slug."""

    if not label:
        return "source"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", label.strip())
    slug = slug.strip("_")
    return slug or "source"


def _coerce_iso(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, str):
        if value.endswith("Z"):
            return value[:-1] + "+00:00"
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _normalise_people(entries: Iterable[Dict[str, Any]] | None) -> List[str]:
    if not entries:
        return []
    people = []
    for person in entries:
        email = person.get("emailAddress") if isinstance(person, dict) else None
        display = person.get("displayName") if isinstance(person, dict) else None
        label = email or display
        if label:
            people.append(label)
    return sorted(dict.fromkeys(people))


def record_sync_snapshot(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Persist metadata about the most recent Drive sync."""

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    aggregated: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "folder_id": None,
            "folder_label": None,
            "folder_slug": None,
            "files": 0,
            "mime_types": defaultdict(int),
            "earliest_modified": None,
            "latest_modified": None,
            "contributors": set(),
        }
    )

    for entry in entries:
        label = entry.get("folder_label") or entry.get("folder_id") or "unknown"
        bucket = aggregated[label]
        bucket["folder_id"] = entry.get("folder_id")
        bucket["folder_label"] = label
        bucket["folder_slug"] = entry.get("folder_slug")
        bucket["files"] += 1
        mime = entry.get("mime_type") or "unknown"
        bucket["mime_types"][mime] += 1

        modified = _coerce_iso(entry.get("modified_time"))
        if modified:
            if bucket["earliest_modified"] is None or modified < bucket["earliest_modified"]:
                bucket["earliest_modified"] = modified
            if bucket["latest_modified"] is None or modified > bucket["latest_modified"]:
                bucket["latest_modified"] = modified

        contributor = entry.get("last_modified_by")
        if contributor:
            bucket["contributors"].add(contributor)
        for owner in _normalise_people(entry.get("owners")):
            bucket["contributors"].add(owner)

    folder_summaries: List[Dict[str, Any]] = []
    for label, bucket in aggregated.items():
        folder_summaries.append(
            {
                "folder_id": bucket["folder_id"],
                "folder_label": label,
                "folder_slug": bucket["folder_slug"],
                "files": bucket["files"],
                "mime_types": dict(sorted(bucket["mime_types"].items(), key=lambda kv: (-kv[1], kv[0]))),
                "earliest_modified": bucket["earliest_modified"],
                "latest_modified": bucket["latest_modified"],
                "contributors": sorted(bucket["contributors"]),
            }
        )

    folder_summaries.sort(key=lambda item: (-(item["files"] or 0), item.get("folder_label") or ""))

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(entries),
        "folders": folder_summaries,
        "entries": entries,
    }

    with SNAPSHOT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2)

    return snapshot


def load_latest_sync() -> Dict[str, Any]:
    """Load the last Drive sync snapshot if available."""

    if not SNAPSHOT_PATH.exists():
        return {}
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


__all__ = ["load_latest_sync", "record_sync_snapshot", "slugify_label"]
