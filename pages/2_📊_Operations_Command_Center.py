"""Streamlit dashboard providing an executive view across recent pipeline runs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config import REPORTS_DIR
st.set_page_config(page_title="Operations Command Center", layout="wide")
st.title("📊 Operations Command Center")

history_path = REPORTS_DIR / "run_history.csv"
if not history_path.exists():
    st.info("Run the pipeline to populate the operations command center.")
    st.stop()

history = pd.read_csv(history_path)
if "timestamp" in history.columns:
    history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
    history = history.sort_values("timestamp")

if history.empty:
    st.info("History is empty. Execute the pipeline to generate metrics.")
    st.stop()

latest_summary_path = REPORTS_DIR / "latest_summary.json"
latest_summary = {}
if latest_summary_path.exists():
    with latest_summary_path.open(encoding="utf-8") as fh:
        latest_summary = json.load(fh)

latest_row = history.iloc[-1]
previous_row = history.iloc[-2] if len(history) > 1 else None

st.caption(
    f"Total recorded runs: {len(history)} | First run: {history['timestamp'].min()} | Last run: {history['timestamp'].max()}"
)
if len(history) > 1:
    cadence = history["timestamp"].diff().dropna().median()
    if pd.notna(cadence):
        st.caption(f"Median cadence between runs: {cadence}")

col1, col2, col3, col4, col5 = st.columns(5)

if "kpi_oee" in latest_row:
    oee_curr = float(latest_row.get("kpi_oee", 0)) * 100
    oee_delta = (
        (oee_curr - float(previous_row.get("kpi_oee", 0)) * 100)
        if previous_row is not None and pd.notna(previous_row.get("kpi_oee"))
        else 0
    )
    col1.metric("OEE", f"{oee_curr:.1f}%", f"{oee_delta:+.1f} pts" if previous_row is not None else None)

if "kpi_fpy" in latest_row:
    fpy_curr = float(latest_row.get("kpi_fpy", 0)) * 100
    fpy_delta = (
        (fpy_curr - float(previous_row.get("kpi_fpy", 0)) * 100)
        if previous_row is not None and pd.notna(previous_row.get("kpi_fpy"))
        else 0
    )
    col2.metric("First Pass Yield", f"{fpy_curr:.1f}%", f"{fpy_delta:+.1f} pts" if previous_row is not None else None)

if "kpi_production" in latest_row:
    prod_curr = float(latest_row.get("kpi_production", 0))
    prod_delta = (
        prod_curr - float(previous_row.get("kpi_production", 0))
        if previous_row is not None and pd.notna(previous_row.get("kpi_production"))
        else 0
    )
    col3.metric("Units Produced", f"{prod_curr:,.0f}", f"{prod_delta:+,.0f}" if previous_row is not None else None)

if "claim_total_claims" in latest_row:
    claim_curr = float(latest_row.get("claim_total_claims", 0))
    claim_delta = (
        claim_curr - float(previous_row.get("claim_total_claims", 0))
        if previous_row is not None and pd.notna(previous_row.get("claim_total_claims"))
    else 0
    )
    col4.metric("Claims Processed", f"{claim_curr:.0f}", f"{claim_delta:+.0f}" if previous_row is not None else None)

if "data_profile_files_profiled" in latest_row:
    files_curr = float(latest_row.get("data_profile_files_profiled", 0))
    files_delta = (
        files_curr - float(previous_row.get("data_profile_files_profiled", 0))
        if previous_row is not None and pd.notna(previous_row.get("data_profile_files_profiled"))
        else 0
    )
    col5.metric(
        "Files Profiled",
        f"{files_curr:.0f}",
        f"{files_delta:+.0f}" if previous_row is not None else None,
    )

st.markdown("---")

performance_tab, quality_tab, documents_tab, actions_tab = st.tabs(
    ["Performance", "Quality", "Documents", "Action Plan"]
)

with performance_tab:
    st.subheader("Throughput & Efficiency")
    if {"kpi_oee", "kpi_fpy"}.intersection(history.columns):
        trend_df = history.dropna(subset=[col for col in ["kpi_oee", "kpi_fpy"] if col in history.columns])
        if not trend_df.empty:
            plot_df = pd.DataFrame({
                "timestamp": trend_df["timestamp"],
            })
            if "kpi_oee" in trend_df.columns:
                plot_df["OEE (%)"] = trend_df["kpi_oee"] * 100
            if "kpi_fpy" in trend_df.columns:
                plot_df["FPY (%)"] = trend_df["kpi_fpy"] * 100
            melt_df = plot_df.melt("timestamp", var_name="Metric", value_name="Percentage")
            fig = px.line(melt_df, x="timestamp", y="Percentage", color="Metric", markers=True)
            fig.update_layout(template="plotly_white", legend_orientation="h")
            fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(fig, use_container_width=True)
    if "kpi_production" in history.columns:
        prod_df = history.dropna(subset=["kpi_production"])
        if not prod_df.empty:
            fig = px.bar(
                prod_df,
                x="timestamp",
                y="kpi_production",
                title="Units Produced per Run",
                labels={"kpi_production": "Units"},
            )
            st.plotly_chart(fig, use_container_width=True)
    kpi_cols = [col for col in history.columns if col.startswith("kpi_")]
    if kpi_cols:
        st.dataframe(history[["timestamp", *kpi_cols]].tail(10))
    else:
        st.info("KPI metrics will appear after data files are processed.")

with quality_tab:
    st.subheader("Claims & Financial Exposure")
    claim_cols = [col for col in history.columns if col.startswith("claim_")]
    if claim_cols:
        claim_df = history.dropna(subset=claim_cols)
        if not claim_df.empty:
            fig = px.bar(
                claim_df,
                x="timestamp",
                y="claim_total_claims",
                hover_data=[c for c in claim_cols if c != "claim_total_claims"],
                title="Claims per Run",
            )
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(claim_df[["timestamp", *claim_cols]].tail(10))
    else:
        st.info("Claims metrics will appear after claim spreadsheets are processed.")

with documents_tab:
    st.subheader("Document Intake Velocity")
    if "document_documents_processed" in history.columns:
        doc_df = history.dropna(subset=["document_documents_processed"])
        if not doc_df.empty:
            fig = px.area(
                doc_df,
                x="timestamp",
                y="document_documents_processed",
                title="Documents Parsed per Run",
            )
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(doc_df[["timestamp", "document_documents_processed"]].tail(10))
    else:
        st.info("Document metrics will populate once text/OCR extraction succeeds.")

with actions_tab:
    st.subheader("Operational Intelligence")
    ai_research = latest_summary.get("ai_research", {}) if latest_summary else {}
    if not ai_research:
        st.info("AI insights become available after the first combined pipeline run.")
    else:
        observations = ai_research.get("observations", [])
        if observations:
            st.markdown("#### Observations")
            for obs in observations:
                st.write(f"- {obs}")
        actions = ai_research.get("next_actions", [])
        if actions:
            st.markdown("#### Next Best Actions")
            for action in actions:
                st.write(f"- {action}")
        integrations = ai_research.get("integrations", {})
        if integrations:
            st.markdown("#### Integration Readiness")
            for name, payload in integrations.items():
                status = payload.get("status", "unknown").title()
                with st.expander(name.replace("_", " ").title()):
                    st.write(f"Status: {status}")
                    if payload.get("error"):
                        st.error(payload["error"])
                    if payload.get("data"):
                        st.json(payload["data"])

st.markdown("---")

st.subheader("Recent Runs")
st.dataframe(history.tail(20), use_container_width=True)
