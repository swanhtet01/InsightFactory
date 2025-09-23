"""Data profiling utilities for InsightFactory ingestion runs."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import os
import re
from typing import Any, Dict, Iterable, List, Set


_GRANULARITY_KEYWORDS = {
    "shift": {"shift"},
    "daily": {"daily"},
    "weekly": {"weekly"},
    "monthly": {"monthly"},
    "hourly": {"hourly"},
    "quarterly": {"quarter", "q1", "q2", "q3", "q4"},
    "yearly": {"annual", "yearly"},
}


def _tokenize(name: str) -> Set[str]:
    tokens = re.split(r"[^A-Za-z0-9]+", name.lower())
    return {token for token in tokens if token}


def _detect_granularity(path: Path) -> Set[str]:
    tokens = _tokenize(path.stem)
    tags: Set[str] = set()
    for label, keywords in _GRANULARITY_KEYWORDS.items():
        if tokens.intersection(keywords):
            tags.add(label)
    return tags


def _relativize(path: Path) -> str:
    try:
        return os.path.relpath(str(path), os.getcwd())
    except ValueError:
        return str(path)


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def profile_files(paths: Iterable[str]) -> Dict[str, Any]:
    """Summarize a collection of files for reporting and dashboards."""

    files = list(paths)
    if not files:
        return {}

    extensions: Counter[str] = Counter()
    total_bytes = 0
    earliest: datetime | None = None
    latest: datetime | None = None
    sample_paths: List[str] = []
    unreadable = 0
    granularities: Set[str] = set()
    unique_paths: Set[str] = set()

    for entry in files:
        path = Path(entry)
        resolved = str(path.resolve())
        if resolved in unique_paths:
            continue
        unique_paths.add(resolved)

        suffix = path.suffix.lower().lstrip(".") or "no_extension"
        extensions[suffix] += 1
        granularities.update(_detect_granularity(path))

        try:
            stat = path.stat()
        except OSError:
            unreadable += 1
            continue

        total_bytes += stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        if earliest is None or mtime < earliest:
            earliest = mtime
        if latest is None or mtime > latest:
            latest = mtime

        sample_paths.append(_relativize(path))

    processed = len(sample_paths)
    sample_preview = sorted(dict.fromkeys(sample_paths))[:8]

    profile: Dict[str, Any] = {
        "inputs_received": len(files),
        "total_files": len(unique_paths),
        "files_profiled": processed,
        "unreadable_files": unreadable,
        "extensions": dict(sorted(extensions.items())),
        "total_bytes": total_bytes,
        "average_bytes": total_bytes / processed if processed else 0,
        "earliest_modified": _isoformat(earliest),
        "latest_modified": _isoformat(latest),
        "sample_files": sample_preview,
        "granularity_tags": sorted(granularities),
    }
    return profile


__all__ = ["profile_files"]
