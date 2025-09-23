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
ai_research = summary.get("ai_research") or {}
performance = summary.get("performance_insights") or {}

last_updated = ai_research.get("metadata", {}).get("generated_at")
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

col4, col5, col6 = st.columns(3)
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

(
    tab_kpi,
    tab_claims,
    tab_documents,
    tab_ai,
    tab_performance,
    tab_history,
    tab_html,
) = st.tabs(
    [
        "KPIs",
        "Claims",
        "Documents",
        "AI Insights",
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
