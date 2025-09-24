"""Evaluate overall system health from pipeline summary outputs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class HealthComponent:
    """Represents an individual health signal."""

    name: str
    score: float
    status: str
    detail: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 1),
            "status": self.status,
            "detail": self.detail,
        }


_STATUS_THRESHOLDS = {
    "excellent": 80,
    "stable": 60,
}


def _score_to_status(score: float) -> str:
    if score >= _STATUS_THRESHOLDS["excellent"]:
        return "excellent"
    if score >= _STATUS_THRESHOLDS["stable"]:
        return "stable"
    return "at_risk"


def _normalize_percentage(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric <= 1:
        numeric *= 100
    return max(0.0, min(100.0, numeric))


def _score_from_range(value: Optional[float], low: float, high: float) -> Optional[float]:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric <= low:
        return 100.0
    if numeric >= high:
        return 0.0
    span = high - low
    return max(0.0, min(100.0, (high - numeric) / span * 100))


def evaluate_system_health(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Combine KPI, claim, document, and profiling context into a health score.

    The output dictionary contains:
    - ``overall_score``: average of all component scores (0-100)
    - ``status``: qualitative label derived from the overall score
    - ``components``: list of component dictionaries with individual statuses
    - ``signals``: ordered list of human-readable insights
    """

    components: List[HealthComponent] = []
    signals: List[str] = []

    kpis = summary.get("kpis") or {}
    if kpis:
        oee_score = _normalize_percentage(kpis.get("oee"))
        if oee_score is not None:
            status = _score_to_status(oee_score)
            components.append(
                HealthComponent(
                    name="OEE",
                    score=oee_score,
                    status=status,
                    detail=f"Overall equipment effectiveness at {oee_score:.1f}%",
                )
            )
            if status == "at_risk":
                signals.append("OEE is below target; investigate availability or performance losses.")
        fpy_score = _normalize_percentage(kpis.get("fpy"))
        if fpy_score is not None:
            status = _score_to_status(fpy_score)
            components.append(
                HealthComponent(
                    name="FPY",
                    score=fpy_score,
                    status=status,
                    detail=f"First pass yield at {fpy_score:.1f}%",
                )
            )
            if status == "at_risk":
                signals.append("First pass yield is low; review defect Pareto charts and containment actions.")

        production = kpis.get("production")
        if production is not None:
            try:
                volume = float(production)
            except (TypeError, ValueError):
                volume = None
            if volume is not None:
                status = "stable" if volume > 0 else "at_risk"
                components.append(
                    HealthComponent(
                        name="Throughput",
                        score=80.0 if volume > 0 else 30.0,
                        status=status,
                        detail=f"Recorded production volume of {volume:.0f} units",
                    )
                )

    claim_metrics = summary.get("claim_metrics") or {}
    if claim_metrics:
        aging = claim_metrics.get("average_days_to_close")
        score = _score_from_range(aging, low=0, high=14)  # two-week SLA
        if score is not None:
            status = _score_to_status(score)
            components.append(
                HealthComponent(
                    name="Claim cycle time",
                    score=score,
                    status=status,
                    detail=f"Average claim close time {float(aging):.1f} days",
                )
            )
            if status == "at_risk":
                signals.append("Claims are aging beyond the two-week SLA; expedite approvals.")
        backlog = claim_metrics.get("open_claims")
        if backlog is not None:
            try:
                open_claims = float(backlog)
            except (TypeError, ValueError):
                open_claims = None
            if open_claims is not None:
                score = _score_from_range(open_claims, low=0, high=25)
                if score is not None:
                    status = _score_to_status(score)
                    components.append(
                        HealthComponent(
                            name="Claim backlog",
                            score=score,
                            status=status,
                            detail=f"{open_claims:.0f} claims waiting for action",
                        )
                    )
                    if status == "at_risk":
                        signals.append("Claim backlog is high; assign owners to clear pending tickets.")

    document_metrics = summary.get("document_metrics") or {}
    unreadable = document_metrics.get("unreadable_documents")
    if unreadable is not None:
        try:
            unreadable_count = float(unreadable)
        except (TypeError, ValueError):
            unreadable_count = None
        if unreadable_count is not None:
            score = _score_from_range(unreadable_count, low=0, high=5)
            if score is not None:
                status = _score_to_status(score)
                components.append(
                    HealthComponent(
                        name="Document quality",
                        score=score,
                        status=status,
                        detail=f"{unreadable_count:.0f} unreadable documents detected",
                    )
                )
                if status == "at_risk":
                    signals.append("Document parsing failures detected; consider OCR retraining or manual review.")

    data_profile = summary.get("data_profile") or {}
    if data_profile:
        freshness = data_profile.get("latest_modified")
        if freshness:
            components.append(
                HealthComponent(
                    name="Data freshness",
                    score=85.0,
                    status="excellent",
                    detail=f"Latest source updated {freshness}",
                )
            )
        unreadable_files = data_profile.get("unreadable_files")
        if unreadable_files:
            score = _score_from_range(unreadable_files, low=0, high=5)
            if score is not None:
                status = _score_to_status(score)
                components.append(
                    HealthComponent(
                        name="Source readability",
                        score=score,
                        status=status,
                        detail=f"{float(unreadable_files):.0f} unreadable files during intake",
                    )
                )
                if status == "at_risk":
                    signals.append("Some source files were unreadable during profiling; verify data exports.")

    if not components:
        return {
            "overall_score": None,
            "status": "unknown",
            "components": [],
            "signals": [
                "No metrics available to evaluate health. Run the pipeline with valid data first.",
            ],
        }

    overall = sum(component.score for component in components) / len(components)
    overall_status = _score_to_status(overall)
    return {
        "overall_score": round(overall, 1),
        "status": overall_status,
        "components": [component.as_dict() for component in components],
        "signals": signals,
    }
