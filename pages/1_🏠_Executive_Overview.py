from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config import REPORTS_DIR


st.set_page_config(page_title="Executive Overview", layout="wide")
st.title("🏠 Executive Overview")

dashboard_path = REPORTS_DIR / "latest_dashboard.json"
if not dashboard_path.exists():
    st.warning("Dashboard dataset not found. Run the unified pipeline to generate reports.")
    st.stop()

with dashboard_path.open(encoding="utf-8") as fh:
    dashboard = json.load(fh)

generated_at = dashboard.get("generated_at")
if generated_at:
    st.caption(f"Last refreshed: {generated_at}")


def _render_metric_card(metric: dict[str, str]) -> None:
    value = metric.get("value", "—")
    delta = metric.get("delta") or None
    label = metric.get("label", "")
    status = metric.get("status")
    help_text = None
    if status == "excellent":
        help_text = "Performance exceeds target range."
    elif status == "stable":
        help_text = (
            "Performance within acceptable range. "
            "Review trends to maintain stability."
        )
    elif status == "attention":
        help_text = (
            "Below target. Prioritise corrective action. "
            "Investigate contributing factors in recent runs."
        )
    st.metric(label, value=value, delta=delta, help=help_text)


hero_metrics = dashboard.get("hero_metrics") or []
if hero_metrics:
    st.subheader("Key Metrics")
    for chunk_start in range(0, len(hero_metrics), 3):
        cols = st.columns(3)
        for col, metric in zip(cols, hero_metrics[chunk_start:chunk_start + 3]):
            with col:
                _render_metric_card(metric)


trend_series = dashboard.get("trend_series") or []
if trend_series:
    st.subheader("Run-to-Run Trends")
    for series in trend_series:
        points = series.get("points") or []
        if not points:
            continue
        df = pd.DataFrame(points)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp", "value"])
        if df.empty:
            continue
        fig = px.line(
            df,
            x="timestamp",
            y="value",
            title=series.get("label", "Trend"),
            labels={"value": series.get("unit", ""), "timestamp": "Run"},
        )
        fig.update_traces(mode="lines+markers")
        if series.get("unit") == "percent":
            fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)


insight_cards = dashboard.get("insight_cards") or []
if insight_cards:
    st.subheader("Insights & Alerts")
    card_columns = st.columns(len(insight_cards))
    for column, card in zip(card_columns, insight_cards):
        with column:
            st.markdown(f"#### {card.get('title', 'Insights')}")
            status = card.get("status")
            if status:
                st.caption(status.replace("_", " ").title())
            for item in card.get("items", []) or []:
                st.markdown(f"- {item}")


next_actions = dashboard.get("next_actions") or []
if next_actions:
    st.subheader("Next Best Actions")
    for action in next_actions:
        st.markdown(f"- ✅ {action}")


health = dashboard.get("system_health") or {}
if health:
    st.subheader("System Health Snapshot")
    cols = st.columns([1, 2])
    with cols[0]:
        overall = health.get("overall_score")
        status = health.get("status")
        label = status.replace("_", " ").title() if isinstance(status, str) else None
        if overall is not None:
            st.metric("Overall Score", f"{float(overall):.1f}", label)
        elif label:
            st.metric("Status", label)
    with cols[1]:
        components = health.get("components") or []
        if components:
            st.dataframe(pd.DataFrame(components))


data_intake = dashboard.get("data_intake") or {}
if data_intake:
    st.subheader("Data Intake Overview")
    intake_cols = st.columns(4)
    intake_cols[0].metric("Files Profiled", f"{data_intake.get('files_profiled', 0)}")
    intake_cols[1].metric("Inputs Received", f"{data_intake.get('inputs_received', 0)}")
    intake_cols[2].metric("Unreadable Files", f"{data_intake.get('unreadable_files', 0)}")
    latest_modified = data_intake.get("latest_modified")
    intake_cols[3].metric("Latest Modified", latest_modified or "—")

    granularity_tags = data_intake.get("granularity_tags") or []
    if granularity_tags:
        st.caption("Detected Granularity: " + ", ".join(granularity_tags))
    sample_files = data_intake.get("sample_files") or []
    if sample_files:
        with st.expander("Sample Files"):
            for item in sample_files:
                st.write(item)
    extensions = data_intake.get("extensions") or {}
    if extensions:
        ext_df = pd.DataFrame(
            [{"Extension": ext, "Files": count} for ext, count in extensions.items()]
        ).sort_values("Files", ascending=False)
        st.dataframe(ext_df, use_container_width=True)


data_sources = dashboard.get("data_sources") or {}
if data_sources:
    st.subheader("Source Coverage")
    st.metric("Tracked Files", f"{data_sources.get('total_files', 0)}")
    folders = data_sources.get("folders") or []
    if folders:
        folder_df = pd.DataFrame(folders)
        st.dataframe(folder_df, use_container_width=True)


st.markdown("---")
st.caption("Built by InsightFactory • Unified analytics, insights, and autonomy in one view.")
