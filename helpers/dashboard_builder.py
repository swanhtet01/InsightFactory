"""Build curated dashboard data structures for UI and API consumers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json

from config import REPORTS_DIR
from helpers.serialization import to_serializable


DASHBOARD_FILENAME = "latest_dashboard.json"


@dataclass(frozen=True)
class HistoryContext:
    """Lightweight wrapper around run-history rows for trend analysis."""

    records: Sequence[Mapping[str, Any]]

    def latest(self) -> Mapping[str, Any] | None:
        return self.records[-1] if self.records else None

    def previous(self) -> Mapping[str, Any] | None:
        return self.records[-2] if len(self.records) > 1 else None

    def trend(self, column: str, scale: float = 1.0) -> list[dict[str, Any]]:
        points: list[dict[str, Any]] = []
        for row in self.records:
            timestamp = row.get("timestamp")
            raw_value = _safe_float(row.get(column))
            if timestamp and raw_value is not None:
                points.append({"timestamp": timestamp, "value": raw_value * scale})
        return points


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_value(value: float | None, unit: str) -> str:
    if value is None:
        return "—"
    if unit == "percent":
        return f"{value:.1f}%"
    if unit == "currency":
        return f"${value:,.2f}"
    if abs(value) >= 1000 and unit == "count":
        return f"{value:,.0f}"
    if unit == "count":
        return f"{value:.0f}"
    return f"{value:.1f}"


def _format_delta(delta: float | None, unit: str) -> str:
    if delta is None:
        return ""
    prefix = "+" if delta >= 0 else ""
    if unit == "percent":
        return f"{prefix}{delta:.1f}pp"
    if unit == "currency":
        return f"{prefix}${delta:,.2f}"
    return f"{prefix}{delta:.0f}"


def _classify_status(metric: str, unit: str, value: float | None) -> str | None:
    if value is None:
        return None
    normalized = value if unit != "percent" else value / 100
    thresholds = {
        "Overall Equipment Effectiveness": (0.85, 0.75),
        "First Pass Yield": (0.95, 0.9),
        "Units Produced": (None, None),
        "Claims Processed": (None, None),
        "Claim Amount": (None, None),
        "Documents Parsed": (None, None),
    }
    good, warn = thresholds.get(metric, (None, None))
    if good is None:
        return None
    if normalized >= good:
        return "excellent"
    if warn is not None and normalized >= warn:
        return "stable"
    return "attention"


def _delta_from_history(history: HistoryContext, column: str, scale: float) -> float | None:
    latest = history.latest()
    previous = history.previous()
    if not latest or not previous:
        return None
    current = _safe_float(latest.get(column))
    past = _safe_float(previous.get(column))
    if current is None or past is None:
        return None
    return (current - past) * scale


def _build_hero_metrics(summary: Mapping[str, Any], history: HistoryContext) -> list[dict[str, Any]]:
    kpis = summary.get("kpis", {}) or {}
    claims = summary.get("claim_metrics", {}) or {}
    documents = summary.get("document_metrics", {}) or {}

    metrics: list[dict[str, Any]] = []
    definitions = [
        (
            "Overall Equipment Effectiveness",
            _safe_float(kpis.get("oee")),
            "kpi_oee",
            100.0,
            "percent",
        ),
        (
            "First Pass Yield",
            _safe_float(kpis.get("fpy")),
            "kpi_fpy",
            100.0,
            "percent",
        ),
        (
            "Units Produced",
            _safe_float(kpis.get("production")),
            "kpi_production",
            1.0,
            "count",
        ),
        (
            "Claims Processed",
            _safe_float(claims.get("total_claims")),
            "claim_total_claims",
            1.0,
            "count",
        ),
        (
            "Claim Amount",
            _safe_float(claims.get("total_claim_amount")),
            "claim_total_claim_amount",
            1.0,
            "currency",
        ),
        (
            "Documents Parsed",
            _safe_float(documents.get("documents_processed")),
            "document_documents_processed",
            1.0,
            "count",
        ),
    ]

    for label, raw_value, column, scale, unit in definitions:
        value = raw_value * scale if raw_value is not None else None
        delta = _delta_from_history(history, column, scale)
        metrics.append(
            {
                "label": label,
                "value": _format_value(value, unit),
                "unit": unit,
                "raw_value": value,
                "delta": _format_delta(delta, unit),
                "status": _classify_status(label, unit, value),
            }
        )
    return metrics


def _collect_insight_cards(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []

    system_health = summary.get("system_health") or {}
    if system_health:
        cards.append(
            {
                "title": "Health Signals",
                "items": (system_health.get("signals") or [])[:5],
                "status": system_health.get("status"),
            }
        )

    performance = summary.get("performance_insights") or {}
    alerts = performance.get("alerts") or []
    forecasts = performance.get("forecast_notes") or []
    if alerts or forecasts:
        cards.append(
            {
                "title": "Performance Outlook",
                "items": (alerts + forecasts)[:5],
                "status": performance.get("trend_status"),
            }
        )

    ai_research = summary.get("ai_research") or {}
    insights = (ai_research.get("observations") or []) + (ai_research.get("risks") or [])
    if insights:
        cards.append(
            {
                "title": "AI Observations",
                "items": insights[:5],
                "status": ai_research.get("status"),
            }
        )

    autonomy = summary.get("autonomy_plan") or {}
    if autonomy.get("immediate_actions"):
        cards.append(
            {
                "title": "Autonomous Actions",
                "items": autonomy.get("immediate_actions")[:5],
                "status": autonomy.get("status"),
            }
        )

    return [card for card in cards if card.get("items")]


def _collect_next_actions(summary: Mapping[str, Any]) -> list[str]:
    next_actions: list[str] = []
    ai_research = summary.get("ai_research") or {}
    autonomy = summary.get("autonomy_plan") or {}

    next_actions.extend(ai_research.get("next_actions") or [])
    next_actions.extend(autonomy.get("opportunities") or [])

    seen: set[str] = set()
    ordered: list[str] = []
    for action in next_actions:
        if action and action not in seen:
            ordered.append(action)
            seen.add(action)
    return ordered[:10]


def _data_intake_panel(summary: Mapping[str, Any]) -> dict[str, Any]:
    profile = summary.get("data_profile") or {}
    return {
        "files_profiled": profile.get("files_profiled") or profile.get("total_files"),
        "inputs_received": profile.get("inputs_received"),
        "unreadable_files": profile.get("unreadable_files"),
        "granularity_tags": profile.get("granularity_tags") or [],
        "sample_files": profile.get("sample_files") or [],
        "extensions": profile.get("extensions") or {},
        "latest_modified": profile.get("latest_modified"),
    }


def _data_sources_panel(summary: Mapping[str, Any]) -> dict[str, Any]:
    sources = summary.get("data_sources") or {}
    folders = sources.get("folders") or []
    by_folder: list[dict[str, Any]] = []
    for folder in folders[:10]:
        by_folder.append(
            {
                "label": folder.get("folder_label") or folder.get("folder_id"),
                "files": folder.get("files"),
                "latest_modified": folder.get("latest_modified"),
                "contributors": folder.get("contributors") or [],
            }
        )
    return {
        "total_files": sources.get("total_files"),
        "folders": by_folder,
    }


def _trend_series(history: HistoryContext) -> list[dict[str, Any]]:
    mapping = [
        ("Overall Equipment Effectiveness", "kpi_oee", 100.0, "percent"),
        ("First Pass Yield", "kpi_fpy", 100.0, "percent"),
        ("Units Produced", "kpi_production", 1.0, "count"),
        ("Claims Processed", "claim_total_claims", 1.0, "count"),
    ]
    series: list[dict[str, Any]] = []
    for label, column, scale, unit in mapping:
        points = history.trend(column, scale)
        if points:
            series.append({"label": label, "unit": unit, "points": points})
    return series


def build_dashboard_payload(
    summary: Mapping[str, Any],
    history_records: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create an aggregated dashboard payload from pipeline outputs."""

    history = HistoryContext(tuple(history_records or ()))
    run_metadata = summary.get("run_metadata") or {}

    payload = {
        "generated_at": run_metadata.get("started_at")
        or (history.latest() or {}).get("timestamp"),
        "hero_metrics": _build_hero_metrics(summary, history),
        "insight_cards": _collect_insight_cards(summary),
        "next_actions": _collect_next_actions(summary),
        "data_intake": _data_intake_panel(summary),
        "data_sources": _data_sources_panel(summary),
        "trend_series": _trend_series(history),
        "system_health": summary.get("system_health") or {},
    }
    return payload


def write_dashboard(summary: Mapping[str, Any], history_records: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Persist the latest dashboard payload alongside other reports."""

    payload = build_dashboard_payload(summary, history_records)
    output = REPORTS_DIR / DASHBOARD_FILENAME
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        json.dump(to_serializable(payload), fh, indent=2)
    return payload


__all__ = ["build_dashboard_payload", "write_dashboard", "DASHBOARD_FILENAME"]
