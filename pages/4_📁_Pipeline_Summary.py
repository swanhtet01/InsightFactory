import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pipeline Summary", layout="wide")
st.title("📁 Pipeline Summary")

summary_path = Path("reports/latest_summary.json")
if not summary_path.exists():
    st.warning("No summary report found. Run the pipeline first.")
    st.stop()

with summary_path.open() as f:
    summary = json.load(f)

st.subheader("KPI Metrics")
st.dataframe(pd.DataFrame([summary.get("kpis", {})]))

st.subheader("Claim Metrics")
st.dataframe(pd.DataFrame([summary.get("claim_metrics", {})]))

st.subheader("Document Metrics")
document_metrics = summary.get("document_metrics", {})
if isinstance(document_metrics, dict):
    st.dataframe(pd.DataFrame([document_metrics]))
else:
    st.dataframe(pd.DataFrame(document_metrics))

ai_research = summary.get("ai_research")
if ai_research:
    st.subheader("AI Research Insights")
    st.markdown("### Observations")
    for obs in ai_research.get("observations", []):
        st.write(f"- {obs}")

    st.markdown("### Next Actions")
    for action in ai_research.get("next_actions", []):
        st.write(f"- {action}")

    st.markdown("### Tooling Roadmap")
    tooling = ai_research.get("tooling", {})
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

    if ai_research.get("metadata"):
        st.caption(f"Generated: {ai_research['metadata'].get('generated_at', 'unknown')}")

html_path = Path("reports/latest_summary.html")
if html_path.exists():
    st.subheader("HTML Report")
    html = html_path.read_text()
    st.components.v1.html(html, height=400, scrolling=True)
