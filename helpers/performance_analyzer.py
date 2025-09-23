"""Analyze run history to surface performance trends and alerts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from .run_history import HISTORY_PATH


@dataclass(frozen=True)
class MetricConfig:
    """Configuration describing how to interpret a historical metric."""

    column: str
    label: str
    direction: str  # "up" means higher is better, "down" means lower is better
    unit: str = ""
    scale: float = 1.0
    minimum_delta: float = 0.0  # minimum absolute delta (in scaled units) to mark as meaningful
    alert_below: Optional[float] = None  # threshold for metrics where higher is better
    alert_above: Optional[float] = None  # threshold for metrics where lower is better
    volatility_threshold: float = 0.2  # coefficient of variation threshold for volatility warnings
    window: int = 5


METRICS: tuple[MetricConfig, ...] = (
    MetricConfig(
        column="kpi_oee",
        label="Overall Equipment Effectiveness",
        direction="up",
        unit="%",
        scale=100.0,
        minimum_delta=0.5,
        alert_below=0.82,
        volatility_threshold=0.05,
    ),
    MetricConfig(
        column="kpi_fpy",
        label="First Pass Yield",
        direction="up",
        unit="%",
        scale=100.0,
        minimum_delta=0.5,
        alert_below=0.9,
        volatility_threshold=0.04,
    ),
    MetricConfig(
        column="kpi_production",
        label="Units Produced",
        direction="up",
        unit="units",
        minimum_delta=10.0,
        volatility_threshold=0.15,
    ),
    MetricConfig(
        column="claim_total_claims",
        label="Claims Submitted",
        direction="down",
        unit="claims",
        minimum_delta=1.0,
        alert_above=50.0,
        volatility_threshold=0.2,
    ),
    MetricConfig(
        column="claim_total_claim_amount",
        label="Claim Exposure",
        direction="down",
        unit="currency",
        minimum_delta=500.0,
        alert_above=10000.0,
        volatility_threshold=0.25,
    ),
    MetricConfig(
        column="document_documents_processed",
        label="Documents Parsed",
        direction="up",
        unit="documents",
        minimum_delta=1.0,
        volatility_threshold=0.25,
    ),
)


def _load_history(path: Path = HISTORY_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        history = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    if "timestamp" in history.columns:
        history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
    return history


def _polyfit_slope(values: pd.Series) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    y = values.to_numpy(dtype=float)
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def _status_from_slope(slope: float, direction: str, significant: bool) -> str:
    if not significant or abs(slope) < 1e-9:
        return "stable"
    if direction == "up":
        return "improving" if slope > 0 else "declining"
    return "improving" if slope < 0 else "declining"


def _format_unit(value: float, unit: str) -> str:
    if unit == "%":
        return f"{value:.1f}%"
    if unit in {"currency"}:
        return f"${value:,.2f}"
    return f"{value:.1f} {unit}".strip()


def _volatility_message(metric: MetricConfig, window_values: pd.Series) -> Optional[str]:
    if len(window_values) < 3:
        return None
    mean = window_values.mean()
    if mean == 0 or pd.isna(mean):
        return None
    std = window_values.std(ddof=0)
    if pd.isna(std) or std == 0:
        return None
    coefficient = abs(std / mean)
    if coefficient >= metric.volatility_threshold:
        return (
            f"{metric.label} is volatile (CV={coefficient:.2f}). Investigate process stability "
            "and upstream drivers."
        )
    return None


def generate_performance_insights(
    summary: Dict[str, Any],
    history_path: Path = HISTORY_PATH,
    metrics: Iterable[MetricConfig] = METRICS,
) -> Dict[str, Any]:
    """Analyze recent history and surface trend insights for dashboards."""

    history = _load_history(history_path)
    insights: Dict[str, Any] = {
        "trends": [],
        "alerts": [],
        "opportunities": [],
        "volatility": [],
        "notes": [],
    }

    if history.empty:
        insights["notes"].append("Run history is empty. Capture at least two runs to unlock trends.")
        return insights

    for metric in metrics:
        if metric.column not in history.columns:
            continue
        series = history[metric.column].dropna()
        if series.empty:
            continue
        window = min(len(series), metric.window)
        window_values = series.tail(window)

        if len(window_values) < 2:
            insights["notes"].append(
                f"Not enough samples to compute a trend for {metric.label}. Run the pipeline again."
            )
            continue

        slope = _polyfit_slope(window_values)
        current = float(window_values.iloc[-1])
        previous = float(window_values.iloc[-2])
        change = current - previous
        scaled_change = change * metric.scale
        scaled_current = current * metric.scale
        scaled_previous = previous * metric.scale
        cumulative_change = (window_values.iloc[-1] - window_values.iloc[0]) * metric.scale

        significant = abs(cumulative_change) >= metric.minimum_delta
        status = _status_from_slope(slope, metric.direction, significant)

        trend_entry = {
            "metric": metric.label,
            "status": status,
            "current": scaled_current,
            "previous": scaled_previous,
            "change": scaled_change,
            "window": window,
            "direction": metric.direction,
            "unit": metric.unit,
            "trend_per_run": slope * metric.scale,
            "cumulative_change": cumulative_change,
        }
        insights["trends"].append(trend_entry)

        if metric.alert_below is not None and scaled_current < metric.alert_below * metric.scale:
            insights["alerts"].append(
                f"{metric.label} fell below the target threshold ({_format_unit(scaled_current, metric.unit)})."
            )
        if metric.alert_above is not None and scaled_current > metric.alert_above:
            insights["alerts"].append(
                f"{metric.label} exceeded the allowable range ({_format_unit(scaled_current, metric.unit)})."
            )

        if status == "improving":
            if metric.direction == "up":
                insights["opportunities"].append(
                    f"{metric.label} is trending upward — amplify what worked this cycle."
                )
            else:
                insights["opportunities"].append(
                    f"{metric.label} is declining, reducing exposure. Capture the lessons learned."
                )
        elif status == "declining":
            if metric.direction == "up":
                insights["alerts"].append(
                    f"{metric.label} is trending downward. Mobilize a countermeasure plan."
                )
            else:
                insights["alerts"].append(
                    f"{metric.label} is increasing. Investigate the root causes immediately."
                )

        volatility_message = _volatility_message(metric, window_values)
        if volatility_message:
            insights["volatility"].append(volatility_message)

    if not insights["trends"]:
        insights["notes"].append("No analyzable metrics found in the run history.")

    return insights
