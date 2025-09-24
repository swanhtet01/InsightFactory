from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st

from config import REPORTS_DIR


st.set_page_config(page_title="InsightFactory Control Center", layout="wide")
st.title("🚀 InsightFactory Control Center")

LATEST_SUMMARY = REPORTS_DIR / "latest_summary.json"
LATEST_DASHBOARD = REPORTS_DIR / "latest_dashboard.json"
RUN_HISTORY = REPORTS_DIR / "run_history.csv"


def _load_json(path: Path) -> dict[str, Any] | None:
    """Return parsed JSON if the file exists."""

    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        st.error(f"{path.name} is not valid JSON. Rerun the pipeline to refresh artifacts.")
        return None


def _format_timestamp(raw: str | None) -> str | None:
    if not raw:
        return None
    parsed = pd.to_datetime(raw, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%d %b %Y • %H:%M UTC")


def _render_metrics(metrics: Iterable[dict[str, Any]]) -> None:
    metrics = list(metrics)
    for offset in range(0, len(metrics), 3):
        cols = st.columns(3)
        for column, metric in zip(cols, metrics[offset : offset + 3]):
            label = metric.get("label", "Metric")
            value = metric.get("value", "—")
            delta = metric.get("delta")
            status = metric.get("status")
            help_text = None
            if status == "excellent":
                help_text = "Performance exceeds the configured target range."
            elif status == "stable":
                help_text = "Within expected bounds. Keep monitoring upcoming runs."
            elif status == "attention":
                help_text = "Below plan. Inspect root causes in the Pipeline Summary."
            column.metric(label, value, delta=delta, help=help_text)


def _render_bullets(title: str, items: Iterable[str]) -> None:
    items = [item for item in items if item]
    if not items:
        return
    st.markdown(f"#### {title}")
    for item in items:
        st.markdown(f"- {item}")


def _render_run_history(path: Path, limit: int = 10) -> None:
    if not path.exists():
        return
    try:
        history = pd.read_csv(path)
    except Exception:
        st.warning("Could not parse run_history.csv. Delete the file and rerun the pipeline.")
        return
    if history.empty:
        return
    history = history.tail(limit).copy()
    if "timestamp" in history.columns:
        history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
        history["timestamp"] = history["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(history, use_container_width=True, hide_index=True)


def _render_data_profile(profile: dict[str, Any]) -> None:
    counts = {
        "Inputs": profile.get("inputs_received"),
        "Files Profiled": profile.get("files_profiled"),
        "Unreadable": profile.get("unreadable_files"),
        "Extensions": ", ".join(
            f"{ext}×{count}" for ext, count in sorted((profile.get("extensions") or {}).items())
        ),
    }
    cols = st.columns(len(counts))
    for column, (label, value) in zip(cols, counts.items()):
        column.metric(label, value if value is not None else "—")
    if profile.get("granularity_tags"):
        st.caption("Detected granularity: " + ", ".join(profile["granularity_tags"]))
    if profile.get("sample_files"):
        with st.expander("Sample files profiled"):
            for sample in profile["sample_files"]:
                st.write(sample)


def _render_freshness(freshness: dict[str, Any]) -> None:
    if not freshness:
        return

    status = freshness.get("status")
    message = freshness.get("message") or "Pipeline run status unavailable."
    last_run = _format_timestamp(freshness.get("last_run_at"))
    age_minutes = freshness.get("age_minutes")

    details = message
    if age_minutes is not None:
        details += f" (Age: {age_minutes:.1f} minutes)"
    if last_run:
        details += f" Last run: {last_run}."

    renderer = {
        "fresh": st.success,
        "stale": st.warning,
        "overdue": st.error,
    }.get(status, st.info)

    renderer(details)


summary = _load_json(LATEST_SUMMARY)
dashboard = _load_json(LATEST_DASHBOARD)

if not summary:
    st.info(
        "Run the unified pipeline to generate analytics before launching the dashboard. "
        "Use the CLI below or start the Drive watcher for continuous updates."
    )
    st.code("python -m helpers.pipeline_runner data", language="bash")
    st.stop()

run_metadata = summary.get("run_metadata", {})
refreshed_at = _format_timestamp(run_metadata.get("started_at")) or _format_timestamp(
    (dashboard or {}).get("generated_at")
)
if refreshed_at:
    st.caption(f"Last refreshed: {refreshed_at}")

overview_tab, data_tab, guidance_tab = st.tabs([
    "Overview",
    "Data Intake",
    "Operations Guide",
])

with overview_tab:
    st.subheader("Latest Run Snapshot")
    _render_freshness(dashboard.get("freshness") if dashboard else None)
    overview_cols = st.columns(4)
    overview_cols[0].metric("Files Processed", run_metadata.get("files_collected", "—"))
    overview_cols[1].metric("Duration (s)", run_metadata.get("duration_seconds", "—"))
    overview_cols[2].metric("Reports Generated", len(run_metadata.get("reports_written", [])))
    overview_cols[3].metric("Sources Tracked", run_metadata.get("sources_tracked", "—"))

    health = summary.get("system_health") or {}
    if health:
        st.subheader("System Health")
        health_cols = st.columns([1, 2])
        overall_score = health.get("overall_score")
        status = health.get("status")
        label = status.replace("_", " ").title() if isinstance(status, str) else None
        health_cols[0].metric(
            "Overall Score",
            f"{overall_score:.1f}" if isinstance(overall_score, (float, int)) else "—",
            label,
        )
        components = health.get("components")
        if components:
            health_cols[1].dataframe(pd.DataFrame(components), use_container_width=True)

    if dashboard and dashboard.get("hero_metrics"):
        st.subheader("Hero Metrics")
        _render_metrics(dashboard["hero_metrics"])

    insights = summary.get("performance_insights", {})
    with st.expander("Performance insights", expanded=bool(insights)):
        _render_bullets("Trend Highlights", insights.get("trends", []))
        _render_bullets("Alerts", insights.get("alerts", []))
        _render_bullets("Opportunities", insights.get("opportunities", []))
        _render_bullets("Forecast", insights.get("forecast_notes", insights.get("forecasts", [])))
        _render_bullets("Volatility", insights.get("volatility", []))

    autonomy = summary.get("autonomy_plan", {})
    with st.expander("Autonomous operations plan", expanded=False):
        _render_bullets("Immediate Actions", autonomy.get("actions", []))
        _render_bullets("Automation Opportunities", autonomy.get("automation_opportunities", []))
        _render_bullets("Readiness", autonomy.get("agent_readiness", []))

    st.subheader("Recent Runs")
    _render_run_history(RUN_HISTORY)

    st.divider()
    st.subheader("Explore the full experience")
    nav_cols = st.columns(3)
    nav_cols[0].page_link("pages/1_🏠_Executive_Overview.py", label="Executive Overview")
    nav_cols[1].page_link("pages/2_📊_Operations_Command_Center.py", label="Operations Command Center")
    nav_cols[2].page_link("pages/4_📁_Pipeline_Summary.py", label="Pipeline Summary")
    st.page_link("pages/5_🤖_AI_Operations_Copilot.py", label="AI Operations Copilot", icon="🤖")

with data_tab:
    st.subheader("Data Intake Profile")
    profile = summary.get("data_profile")
    if profile:
        _render_data_profile(profile)
    else:
        st.info("Run the pipeline with the profiling helper enabled to see intake statistics.")

    data_sources = summary.get("data_sources")
    if data_sources:
        st.markdown("#### Source Coverage")
        st.metric("Tracked Files", data_sources.get("total_files", "—"))
        folders = data_sources.get("folders")
        if folders:
            st.dataframe(pd.DataFrame(folders), use_container_width=True)

with guidance_tab:
    st.subheader("Keep the analytics fresh")
    st.markdown(
        "Run the unified pipeline whenever new spreadsheets, claims, or documents land in your Drive folders."
    )
    st.code("python -m helpers.pipeline_runner <file-or-directory> [...]")
    st.markdown(
        "Launch the Drive watcher for hands-free updates once credentials are configured:"
    )
    st.code("python helpers/drive_watcher.py")
    st.markdown("Expose insights to downstream tools via the REST API:")
    st.code("uvicorn api:app --reload")
    st.markdown(
        "Need help wiring CopilotKit or Tongyi DeepResearch? Visit the AI Operations Copilot page for status and next steps."
    )
