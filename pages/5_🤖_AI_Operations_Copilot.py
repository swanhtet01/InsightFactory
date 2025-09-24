import json
from pathlib import Path

import streamlit as st

from helpers.research_planner import ResearchPlanner
from config import REPORTS_DIR

st.set_page_config(page_title="AI Operations Copilot", layout="wide")
st.title("🤖 AI Operations Copilot")

summary_path = REPORTS_DIR / "latest_summary.json"
if not summary_path.exists():
    st.warning(
        f"Run the unified pipeline to generate `{summary_path}`."
    )
    st.stop()

summary = json.loads(summary_path.read_text(encoding="utf-8"))
planner = ResearchPlanner.from_env()

if st.button("Refresh insights using current environment credentials"):
    summary["ai_research"] = planner.generate_insights(summary)
    st.success("Regenerated AI research insights.")

ai_research = summary.get("ai_research", {})

col1, col2 = st.columns(2)
with col1:
    st.subheader("Observations")
    for obs in ai_research.get("observations", []):
        st.write(f"- {obs}")
with col2:
    st.subheader("Next Actions")
    for action in ai_research.get("next_actions", []):
        st.write(f"- {action}")

st.markdown("---")
st.subheader("Tooling Integrations")
tooling = ai_research.get("tooling", {})
for name, plan in tooling.items():
    status = "✅" if plan.get("enabled") else "⚪"
    st.markdown(f"### {status} {name.replace('_', ' ').title()}")
    if plan.get("note"):
        st.info(plan["note"])
    if plan.get("documentation"):
        st.markdown(f"[Documentation Link]({plan['documentation']})")
    if plan.get("recommended_steps"):
        for step in plan["recommended_steps"]:
            st.write(f"- {step}")

st.markdown("---")
st.subheader("Live API Responses")
integrations = ai_research.get("integrations", {})
if not integrations:
    st.info("No integration responses captured; configure API bases to enable live calls.")
else:
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
    st.caption(
        f"Generated at {ai_research['metadata'].get('generated_at', 'unknown')} | "
        f"CopilotKit Enabled: {ai_research['metadata'].get('copilotkit_enabled')} | "
        f"DeepResearch Enabled: {ai_research['metadata'].get('deep_research_enabled')}"
    )
