"""Generate autonomous operations plans based on pipeline output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AgentStatus:
    """Describe the state of an autonomous agent hook."""

    name: str
    status: str
    description: str
    triggers: List[str]
    next_steps: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "description": self.description,
            "triggers": self.triggers,
            "next_steps": self.next_steps,
        }


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _agent_status(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    run_metadata = summary.get("run_metadata") or {}
    data_sources = summary.get("data_sources") or {}
    performance = summary.get("performance_insights") or {}
    ai_research = summary.get("ai_research") or {}

    source_count = 0
    if isinstance(data_sources, dict):
        folders = data_sources.get("folders") or []
        source_count = len(folders)

    watcher_status = "ready" if run_metadata else "pending"
    if run_metadata and run_metadata.get("files_collected", 0) == 0:
        watcher_status = "idle"

    trends = performance.get("trends") or []
    forecast_ready = "ready" if trends else "pending"

    copilot_status = ai_research.get("integrations", {}).get("copilotkit", {}).get("status")
    deep_status = ai_research.get("integrations", {}).get("deep_research", {}).get("status")
    research_ready = "ready" if copilot_status == "ok" or deep_status == "ok" else "pending"

    agents = [
        AgentStatus(
            name="Drive Sync Watcher",
            status=watcher_status,
            description=(
                "Monitors shared Google Drive folders ("
                f"tracking {source_count} source(s)) and triggers the unified pipeline when files change."
            ),
            triggers=[
                "Drive API change notifications",
                "Manual pipeline_runner CLI invocation",
            ],
            next_steps=[
                "Deploy helpers.drive_watcher on an always-on VM or container.",
                "Configure GOOGLE_DRIVE_FOLDER_IDS and credentials via environment variables.",
            ],
        ),
        AgentStatus(
            name="KPI Forecaster",
            status=forecast_ready,
            description="Projects future KPI levels using the latest run history to keep teams ahead of emerging risks.",
            triggers=[
                "Completion of pipeline runs",
                "New rows appended to reports/run_history.csv",
            ],
            next_steps=[
                "Automate post-run notifications that include forecast deltas.",
                "Feed projections into CopilotKit for conversational planning.",
            ],
        ),
        AgentStatus(
            name="AI Research Escalation",
            status=research_ready,
            description="Routes significant KPI shifts or claim exposure spikes to CopilotKit or Tongyi DeepResearch for deeper analysis.",
            triggers=[
                "Performance analyzer alerts",
                "CopilotKit/Tongyi DeepResearch availability",
            ],
            next_steps=[
                "Provide API base URLs and keys for the selected research tools.",
                "Record recommendations in run history for longitudinal tracking.",
            ],
        ),
    ]

    return [agent.to_dict() for agent in agents]


def generate_autonomy_plan(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize a pragmatic plan for autonomous operations."""

    kpis = summary.get("kpis") or {}
    claims = summary.get("claim_metrics") or {}
    documents = summary.get("document_metrics") or {}
    data_profile = summary.get("data_profile") or {}
    performance = summary.get("performance_insights") or {}
    ai_research = summary.get("ai_research") or {}

    immediate: List[str] = []
    automation: List[str] = []
    monitoring: List[str] = []

    oee = _safe_float(kpis.get("oee"))
    if oee is not None and oee < 0.85:
        immediate.append(
            "Spin up a downtime root-cause squad and schedule hourly availability sampling until OEE exceeds 85%."
        )

    fpy = _safe_float(kpis.get("fpy"))
    if fpy is not None and fpy < 0.95:
        immediate.append(
            "Deploy an inspection feedback agent to capture defect causes at the machine level and close the FPY gap."
        )

    unreadable = data_profile.get("unreadable_files")
    if isinstance(unreadable, (int, float)) and unreadable > 0:
        immediate.append(
            "Review unreadable files and extend OCR/parsing coverage so every production artifact feeds the data lake."
        )

    total_claims = _safe_float(claims.get("total_claims"))
    if total_claims and total_claims > 25:
        immediate.append(
            "Escalate claim backlog to the AI Research Escalation agent for batching and prioritization."
        )

    integrations = ai_research.get("integrations", {})
    copilot_status = integrations.get("copilotkit", {}).get("status")
    deep_status = integrations.get("deep_research", {}).get("status")
    if copilot_status != "ok":
        automation.append(
            "Connect CopilotKit to the FastAPI/Streamlit surface so operators can request live playbooks."
        )
    if deep_status != "ok":
        automation.append(
            "Provision Tongyi DeepResearch credentials and automate weekly research prompts around KPI deltas."
        )

    if performance.get("alerts"):
        monitoring.extend(performance["alerts"])
    if performance.get("volatility"):
        monitoring.extend(performance["volatility"])

    if documents and documents.get("documents_processed") == 0:
        monitoring.append(
            "No documents processed in the last run; ensure watcher permissions cover every shared folder."
        )

    if not monitoring:
        monitoring.append("No outstanding alerts. Continue monitoring automated runs.")

    plan = {
        "immediate_actions": immediate
        or ["System stable. Continue automated monitoring and focus on strategic enhancements."],
        "automation_opportunities": automation
        or ["Autonomous tooling fully configured. Expand coverage with additional plant data feeds."],
        "monitoring": monitoring,
        "agents": _agent_status(summary),
    }

    return plan
