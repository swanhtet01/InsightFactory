from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Pipeline Summary", layout="wide")
st.title("📁 Pipeline Summary")

summary_path = Path("reports/latest_summary.json")
if not summary_path.exists():
    st.warning("No summary report found. Run the pipeline first.")
    st.stop()

with summary_path.open(encoding="utf-8") as f:
    summary = json.load(f)

history_path = Path("reports/run_history.csv")
history_df = None
if history_path.exists():
    history_df = pd.read_csv(history_path)
    if "timestamp" in history_df.columns:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], errors="coerce")
        history_df = history_df.sort_values("timestamp")

kpis = summary.get("kpis", {})
claims = summary.get("claim_metrics", {})
documents = summary.get("document_metrics", {})
data_profile = summary.get("data_profile", {})
data_sources = summary.get("data_sources") or {}
run_metadata = summary.get("run_metadata", {})
ai_research = summary.get("ai_research") or {}
performance = summary.get("performance_insights") or {}
system_health = summary.get("system_health") or {}

last_updated = ai_research.get("metadata", {}).get("generated_at")
if not last_updated and run_metadata.get("started_at"):
    last_updated = run_metadata["started_at"]
if not last_updated and history_df is not None and not history_df.empty:
    last_updated = history_df.iloc[-1]["timestamp"]
if last_updated:
    st.caption(f"Last refreshed: {last_updated}")


def _metric_delta(column: str, scale: float = 1.0) -> tuple[str, str]:
    if history_df is None or len(history_df) < 2 or column not in history_df.columns:
        return "", ""
    curr = history_df.iloc[-1][column]
    prev = history_df.iloc[-2][column]
    if pd.isna(curr) or pd.isna(prev):
        return "", ""
    delta = (curr - prev) * scale
    return f"{curr * scale:.1f}", f"{delta:+.1f}"


st.subheader("Executive Snapshot")
col1, col2, col3 = st.columns(3)

if kpis:
    _, oee_delta = _metric_delta("kpi_oee", scale=100)
    _, fpy_delta = _metric_delta("kpi_fpy", scale=100)
    _, prod_delta = _metric_delta("kpi_production")
    col1.metric("Overall Equipment Effectiveness", f"{float(kpis.get('oee', 0))*100:.1f}%", oee_delta)
    col2.metric("First Pass Yield", f"{float(kpis.get('fpy', 0))*100:.1f}%", fpy_delta)
    col3.metric("Units Produced", f"{float(kpis.get('production', 0)):.0f}", prod_delta)

col4, col5, col6, col7 = st.columns(4)
if claims:
    total_claims = float(claims.get("total_claims", 0))
    total_amount = float(claims.get("total_claim_amount", 0))
    claims_delta = _metric_delta("claim_total_claims")
    amount_delta = _metric_delta("claim_total_claim_amount")
    col4.metric("Claims Processed", f"{total_claims:.0f}", claims_delta[1])
    col5.metric("Claim Amount", f"{total_amount:,.2f}", amount_delta[1])

if documents:
    docs_delta = _metric_delta("document_documents_processed")
    col6.metric("Documents Parsed", f"{float(documents.get('documents_processed', 0)):.0f}", docs_delta[1])

if data_profile:
    files_delta = _metric_delta("data_profile_total_files")
    col7.metric(
        "Files Profiled",
        f"{int(data_profile.get('files_profiled', data_profile.get('total_files', 0)))}",
        files_delta[1],
    )
else:
    col7.metric("Files Profiled", "0")

st.markdown("### Highlights")
highlights: list[str] = []

if run_metadata:
    duration = run_metadata.get("duration_seconds")
    if duration is not None:
        highlights.append(f"Last run completed in {float(duration):.1f} seconds.")
    reports_written = run_metadata.get("reports_written") or []
    if reports_written:
        highlights.append(
            f"Generated {len(reports_written)} report artifact(s) including {reports_written[-1]}."
        )

if performance:
    notes = performance.get("forecast_notes") or []
    highlights.extend(notes)
    trends = performance.get("alerts") or []
    highlights.extend(trends)

if ai_research:
    next_actions = ai_research.get("next_actions") or []
    highlights.extend(next_actions[:3])
    observations = ai_research.get("observations") or []
    highlights.extend(observations[:2])

autonomy_plan = summary.get("autonomy_plan") or {}
if autonomy_plan:
    immediate = autonomy_plan.get("immediate_actions") or []
    if immediate:
        highlights.append(f"Autonomy plan suggests: {immediate[0]}")

if system_health and system_health.get("signals"):
    highlights.extend(system_health["signals"][:2])

if highlights:
    for item in highlights[:8]:
        st.markdown(f"- {item}")
else:
    st.info("Run the unified pipeline to populate highlights and recommended actions.")

if system_health:
    st.markdown("### Health Scorecard")
    overall = system_health.get("overall_score")
    status = system_health.get("status")
    cols = st.columns([1, 2])
    with cols[0]:
        if overall is not None:
            st.metric("Overall Health", f"{float(overall):.1f}", status.replace("_", " ").title() if status else None)
        elif status:
            st.metric("Overall Health", status.replace("_", " ").title())
    with cols[1]:
        components = system_health.get("components") or []
        if components:
            st.dataframe(pd.DataFrame(components))
        signals = system_health.get("signals") or []
        if signals:
            st.markdown("**Attention Items**")
            for signal in signals:
                st.markdown(f"- {signal}")

(
    tab_kpi,
    tab_claims,
    tab_documents,
    tab_data,
    tab_ai,
    tab_autonomy,
    tab_performance,
    tab_history,
    tab_html,
) = st.tabs(
    [
        "KPIs",
        "Claims",
        "Documents",
        "Data Intake",
        "AI Insights",
        "Autonomy Plan",
        "Performance Insights",
        "Run History",
        "HTML Report",
    ]
)

with tab_kpi:
    st.markdown("### KPI Table")
    st.dataframe(pd.DataFrame([kpis]))
    if history_df is not None and "kpi_oee" in history_df.columns:
        kpi_chart = history_df.dropna(subset=["kpi_oee"])
        if not kpi_chart.empty:
            kpi_chart = kpi_chart.assign(
                oee_pct=kpi_chart["kpi_oee"] * 100,
                fpy_pct=kpi_chart.get("kpi_fpy", pd.Series(dtype=float)) * 100,
            )
            y_columns = [col for col in ["oee_pct", "fpy_pct"] if col in kpi_chart.columns]
            if y_columns:
                fig = px.line(
                    kpi_chart,
                    x="timestamp",
                    y=y_columns,
                    labels={"value": "Percentage", "timestamp": "Run"},
                    title="OEE & FPY Trend",
                )
                fig.update_traces(mode="lines+markers")
                fig.update_yaxes(ticksuffix="%")
                st.plotly_chart(fig, use_container_width=True)
    if history_df is not None and "kpi_production" in history_df.columns:
        prod_chart = history_df.dropna(subset=["kpi_production"])
        if not prod_chart.empty:
            fig = px.bar(
                prod_chart,
                x="timestamp",
                y="kpi_production",
                title="Production Volume per Run",
                labels={"kpi_production": "Units"},
            )
            st.plotly_chart(fig, use_container_width=True)

with tab_claims:
    st.markdown("### Claim Metrics")
    st.dataframe(pd.DataFrame([claims]))
    if history_df is not None and {"claim_total_claims", "claim_total_claim_amount"}.issubset(history_df.columns):
        claim_chart = history_df.dropna(subset=["claim_total_claims"])
        if not claim_chart.empty:
            fig = px.area(
                claim_chart,
                x="timestamp",
                y="claim_total_claims",
                title="Claims Processed per Run",
                labels={"claim_total_claims": "Claims"},
            )
            st.plotly_chart(fig, use_container_width=True)

with tab_documents:
    st.markdown("### Document Metrics")
    if isinstance(documents, dict):
        st.dataframe(pd.DataFrame([documents]))
    else:
        st.dataframe(pd.DataFrame(documents))

with tab_data:
    st.markdown("### Data Intake Overview")
    if not data_profile and not run_metadata:
        st.info("Data profiling metrics will appear after the first run.")
    else:
        if data_profile:
            col_a, col_b, col_c = st.columns(3)
            total_files = int(data_profile.get("total_files", 0))
            files_profiled = int(data_profile.get("files_profiled", total_files))
            unreadable = int(data_profile.get("unreadable_files", 0))
            inputs_received = int(
                data_profile.get("inputs_received", files_profiled)
            )
            col_a.metric("Inputs Received", f"{inputs_received}")
            col_b.metric("Unique Files", f"{total_files}")
            col_c.metric("Files Profiled", f"{files_profiled}")

            size_mb = data_profile.get("total_bytes", 0) / (1024 ** 2)
            avg_kb = (
                data_profile.get("average_bytes", 0) / 1024 if files_profiled else 0
            )
            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric("Data Volume", f"{size_mb:.2f} MB")
            metric_col2.metric("Average File Size", f"{avg_kb:.2f} KB")
            if unreadable:
                st.warning(
                    f"{unreadable} file(s) were unreadable during the last run. Check permissions or formats."
                )

            if data_profile.get("extensions"):
                ext_df = pd.DataFrame(
                    [
                        {"Extension": ext, "Files": count}
                        for ext, count in sorted(
                            data_profile["extensions"].items(),
                            key=lambda kv: (-kv[1], kv[0]),
                        )
                    ]
                )
                st.markdown("#### Files by Type")
                st.dataframe(ext_df, use_container_width=True)

            if data_profile.get("sample_files"):
                st.markdown("#### Sample Files")
                for sample in data_profile["sample_files"]:
                    st.write(f"- {sample}")

            if data_profile.get("granularity_tags"):
                st.markdown("#### Detected Granularity Tags")
                st.write(", ".join(data_profile["granularity_tags"]))

        folders = data_sources.get("folders") if isinstance(data_sources, dict) else []
        if folders:
            st.markdown("### Source Coverage")
            folder_df = pd.DataFrame(folders)
            if not folder_df.empty:
                display_df = folder_df.copy()
                if "contributors" in display_df.columns:
                    display_df["contributors"] = display_df["contributors"].apply(
                        lambda value: ", ".join(value) if isinstance(value, list) else value
                    )
                display_df = display_df.rename(
                    columns={
                        "folder_label": "Folder",
                        "files": "Files",
                        "latest_modified": "Latest Modified",
                        "earliest_modified": "Earliest Modified",
                        "contributors": "Contributors",
                    }
                )
                st.dataframe(
                    display_df[
                        [
                            col
                            for col in [
                                "Folder",
                                "Files",
                                "Latest Modified",
                                "Earliest Modified",
                                "Contributors",
                            ]
                            if col in display_df.columns
                        ]
                    ],
                    use_container_width=True,
                )
            entries = data_sources.get("entries", [])
            if entries:
                st.markdown("#### Latest Files")
                entry_df = pd.DataFrame(entries)
                if not entry_df.empty:
                    if "modified_time" in entry_df.columns:
                        entry_df = entry_df.sort_values("modified_time", ascending=False)
                    st.dataframe(
                        entry_df[
                            [
                                col
                                for col in [
                                    "name",
                                    "folder_label",
                                    "mime_type",
                                    "modified_time",
                                    "local_path",
                                ]
                                if col in entry_df.columns
                            ]
                        ].head(20),
                        use_container_width=True,
                    )

        if run_metadata:
            st.markdown("### Run Metadata")
            meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
            if run_metadata.get("duration_seconds") is not None:
                meta_col1.metric(
                    "Duration (s)",
                    f"{float(run_metadata['duration_seconds']):.2f}",
                )
            if run_metadata.get("files_collected") is not None:
                meta_col2.metric(
                    "Files Collected", f"{int(run_metadata['files_collected'])}"
                )
            if run_metadata.get("files_profiled") is not None:
                meta_col3.metric(
                    "Files Profiled", f"{int(run_metadata['files_profiled'])}"
                )
            if run_metadata.get("sources_tracked") is not None:
                meta_col4.metric(
                    "Sources Tracked",
                    f"{int(run_metadata['sources_tracked'])}",
                )
            if run_metadata.get("reports_written"):
                st.markdown("#### Reports Written")
                for report in run_metadata["reports_written"]:
                    st.write(f"- {report}")

with tab_ai:
    st.markdown("### AI Research Insights")
    observations = ai_research.get("observations", [])
    if observations:
        st.markdown("#### Observations")
        for obs in observations:
            st.write(f"- {obs}")
    actions = ai_research.get("next_actions", [])
    if actions:
        st.markdown("#### Next Actions")
        for action in actions:
            st.write(f"- {action}")
    tooling = ai_research.get("tooling", {})
    if tooling:
        st.markdown("#### Tooling Roadmap")
        for name, plan in tooling.items():
            with st.expander(name.replace("_", " ").title()):
                st.write(f"**Enabled:** {'Yes' if plan.get('enabled') else 'No'}")
                if plan.get("note"):
                    st.info(plan["note"])
                if plan.get("documentation"):
                    st.markdown(f"[Documentation]({plan['documentation']})")
                if plan.get("recommended_steps"):
                    st.markdown("**Recommended Steps**")
                    for step in plan["recommended_steps"]:
                        st.write(f"- {step}")
    integrations = ai_research.get("integrations", {})
    if integrations:
        st.markdown("#### Live Integration Status")
        for name, info in integrations.items():
            status = info.get("status", "unknown")
            icon = "✅" if status == "ok" else "⚪" if status == "disabled" else "⚠️"
            with st.expander(f"{icon} {name.replace('_', ' ').title()}"):
                st.write(f"**Status:** {status}")
                if info.get("error"):
                    st.error(info["error"])
                if info.get("data"):
                    st.json(info["data"])
    if ai_research.get("metadata"):
        st.caption(f"Generated: {ai_research['metadata'].get('generated_at', 'unknown')}")

with tab_autonomy:
    st.markdown("### Autonomous Operations Plan")
    autonomy = summary.get("autonomy_plan") or {}
    if not autonomy:
        st.info("Autonomy planner will populate after the first full pipeline run.")
    else:
        immediate = autonomy.get("immediate_actions") or []
        automation = autonomy.get("automation_opportunities") or []
        monitoring_items = autonomy.get("monitoring") or []

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Immediate Actions")
            if immediate:
                for item in immediate:
                    st.write(f"- {item}")
            else:
                st.write("No urgent actions identified.")
        with col_b:
            st.markdown("#### Automation Opportunities")
            if automation:
                for item in automation:
                    st.write(f"- {item}")
            else:
                st.write("All automation hooks are configured.")

        st.markdown("#### Monitoring Watchlist")
        if monitoring_items:
            for item in monitoring_items:
                st.write(f"- {item}")
        else:
            st.write("No alerts at this time.")

        agents = autonomy.get("agents") or []
        if agents:
            st.markdown("#### Agent Roster")
            agent_df = pd.DataFrame(agents)
            if not agent_df.empty:
                st.dataframe(
                    agent_df.rename(
                        columns={
                            "name": "Agent",
                            "status": "Status",
                            "description": "Description",
                            "triggers": "Triggers",
                            "next_steps": "Next Steps",
                        }
                    ),
                    use_container_width=True,
                )


def _format_metric(value: float, unit: str) -> str:
    if value is None or pd.isna(value):
        return "-"
    if unit == "%":
        return f"{float(value):.1f}%"
    if unit == "currency":
        return f"${float(value):,.2f}"
    if isinstance(value, (int, float)):
        return f"{float(value):.1f}"
    return str(value)


with tab_performance:
    st.markdown("### Performance Trends")
    trends = performance.get("trends") or []
    if trends:
        rows = []
        for entry in trends:
            unit = entry.get("unit", "")
            rows.append(
                {
                    "Metric": entry.get("metric"),
                    "Status": entry.get("status", "").title(),
                    "Current": _format_metric(entry.get("current"), unit),
                    "Previous": _format_metric(entry.get("previous"), unit),
                    "Δ": _format_metric(entry.get("change"), unit),
                    "Δ per Run": _format_metric(entry.get("trend_per_run"), unit),
                    "Window": entry.get("window"),
                }
            )
        st.dataframe(pd.DataFrame(rows))
    else:
        st.info("Trend analytics will appear after at least two runs.")

    alerts = performance.get("alerts") or []
    if alerts:
        st.markdown("#### Alerts")
        for alert in alerts:
            st.error(alert)

    opportunities = performance.get("opportunities") or []
    if opportunities:
        st.markdown("#### Opportunities")
        for note in opportunities:
            st.success(note)

    volatility = performance.get("volatility") or []
    if volatility:
        st.markdown("#### Volatility Watch")
        for msg in volatility:
            st.warning(msg)

    notes = performance.get("notes") or []
    if notes:
        st.markdown("#### Notes")
        for msg in notes:
            st.info(msg)

with tab_history:
    if history_df is None or history_df.empty:
        st.info("History will populate after the first pipeline execution.")
    else:
        st.dataframe(history_df.tail(50), use_container_width=True)

with tab_html:
    html_path = Path("reports/latest_summary.html")
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
        st.components.v1.html(html, height=400, scrolling=True)
    else:
        st.info("HTML report not generated yet.")
