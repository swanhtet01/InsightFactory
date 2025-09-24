"""Utilities for converting complex objects into JSON-friendly structures."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def to_serializable(value: Any) -> Any:
    """Recursively convert objects into JSON-serializable representations."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if hasattr(value, "item"):
        try:
            return to_serializable(value.item())
        except Exception:  # pragma: no cover - fallback to string representation
            return str(value)

    if isinstance(value, Mapping):
        return {str(key): to_serializable(item) for key, item in value.items()}

    if isinstance(value, (set, tuple, list)):
        return [to_serializable(item) for item in value]

    if hasattr(value, "__iter__") and not isinstance(value, (bytes, bytearray)):
        try:
            return [to_serializable(item) for item in value]
        except TypeError:
            pass

    return str(value)


__all__ = ["to_serializable"]
