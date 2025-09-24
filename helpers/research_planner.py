"""Strategic planning helpers for AI research integrations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional
import os

from helpers.integration_clients import (
    CopilotKitClient,
    IntegrationResult,
    TongyiDeepResearchClient,
)
from helpers.serialization import to_serializable


@dataclass
class IntegrationConfig:
    """Configuration flags for optional research integrations."""

    name: str
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    endpoint: Optional[str] = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_base or self.api_key)


class ResearchPlanner:
    """Build action plans using KPI results and optional research tools."""

    def __init__(
        self,
        copilotkit: Optional[IntegrationConfig] = None,
        deep_research: Optional[IntegrationConfig] = None,
        copilotkit_client: Optional[CopilotKitClient] = None,
        deep_research_client: Optional[TongyiDeepResearchClient] = None,
    ) -> None:
        self.copilotkit = copilotkit or IntegrationConfig(name="CopilotKit")
        self.deep_research = deep_research or IntegrationConfig(name="Tongyi DeepResearch")
        self._copilotkit_client = copilotkit_client or CopilotKitClient(
            api_base=self.copilotkit.api_base,
            api_key=self.copilotkit.api_key,
            endpoint=self.copilotkit.endpoint,
        )
        self._deep_research_client = deep_research_client or TongyiDeepResearchClient(
            api_base=self.deep_research.api_base,
            api_key=self.deep_research.api_key,
            endpoint=self.deep_research.endpoint,
        )

    @classmethod
    def from_env(cls) -> "ResearchPlanner":
        """Build a planner using environment variables for credentials."""

        copilot = IntegrationConfig(
            name="CopilotKit",
            api_base=os.getenv("COPILOTKIT_API_BASE"),
            api_key=os.getenv("COPILOTKIT_API_KEY"),
            endpoint=os.getenv("COPILOTKIT_INSIGHTS_PATH", "/api/v1/insights"),
        )
        deep_research = IntegrationConfig(
            name="Tongyi DeepResearch",
            api_base=os.getenv("DEEPRESEARCH_API_BASE"),
            api_key=os.getenv("DEEPRESEARCH_API_KEY"),
            endpoint=os.getenv("DEEPRESEARCH_RESEARCH_PATH", "/api/v1/research"),
        )
        return cls(copilotkit=copilot, deep_research=deep_research)

    def generate_insights(self, summary: Dict[str, Dict]) -> Dict[str, object]:
        """Return strategic recommendations derived from pipeline output."""

        actions = self._baseline_actions(summary)
        observations = self._observations(summary)
        integrations = self._integration_runs(summary)
        tooling = {
            "copilotkit": self._copilotkit_plan(),
            "deep_research": self._deep_research_plan(),
        }
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "copilotkit_enabled": self.copilotkit.enabled,
            "deep_research_enabled": self.deep_research.enabled,
            "copilotkit_status": integrations["copilotkit"].get("status"),
            "deep_research_status": integrations["deep_research"].get("status"),
        }
        return {
            "next_actions": actions,
            "observations": observations,
            "tooling": tooling,
            "integrations": integrations,
            "metadata": metadata,
        }

    def _integration_runs(self, summary: Dict[str, Dict]) -> Dict[str, Dict]:
        def _result_to_dict(result: IntegrationResult) -> Dict[str, object]:
            return result.to_dict()

        sanitized_summary = to_serializable(summary)

        copilotkit_result = (
            self._copilotkit_client.request_brief(sanitized_summary)
            if self._copilotkit_client.enabled
            else IntegrationResult(status="disabled")
        )
        deep_research_result = (
            self._deep_research_client.request_research(sanitized_summary)
            if self._deep_research_client.enabled
            else IntegrationResult(status="disabled")
        )
        return {
            "copilotkit": _result_to_dict(copilotkit_result),
            "deep_research": _result_to_dict(deep_research_result),
        }

    def _baseline_actions(self, summary: Dict[str, Dict]) -> List[str]:
        actions: List[str] = []
        kpis = summary.get("kpis") or {}
        oee = self._to_percentage(kpis.get("oee"))
        fpy = self._to_percentage(kpis.get("fpy"))
        scrap_rate = self._to_percentage(kpis.get("scrap_rate"))

        if oee is not None and oee < 85:
            actions.append(
                "Launch a focused downtime analysis sprint; OEE below 85% indicates availability losses."
            )
        if fpy is not None and fpy < 95:
            actions.append(
                "Run root-cause workshops with quality teams to raise first-pass yield toward 98%."
            )
        if scrap_rate is not None and scrap_rate > 5:
            actions.append(
                "Escalate scrap-reduction kaizen with maintenance and process engineering."
            )

        claims = summary.get("claim_metrics") or {}
        total_claims = claims.get("total_claims")
        total_amount = claims.get("total_claim_amount")
        if isinstance(total_claims, (int, float)) and total_claims > 0:
            actions.append(
                f"Implement CopilotKit-assisted triage for {int(total_claims)} open claims to speed up resolution."
            )
        if isinstance(total_amount, (int, float)) and total_amount > 0:
            actions.append(
                "Benchmark payout amounts against policy to flag outliers for Tongyi DeepResearch review."
            )

        documents = summary.get("document_metrics") or {}
        processed = documents.get("documents_processed")
        if isinstance(processed, (int, float)) and processed == 0:
            actions.append("Expand OCR coverage so new production logs feed analytics automatically.")

        if not actions:
            actions.append(
                "Maintain current operating cadence; KPIs and document pipelines are within expected thresholds."
            )
        return actions

    def _observations(self, summary: Dict[str, Dict]) -> List[str]:
        observations: List[str] = []
        kpis = summary.get("kpis") or {}
        oee = self._to_percentage(kpis.get("oee"))
        fpy = self._to_percentage(kpis.get("fpy"))
        production = kpis.get("production")
        target_achievement = self._to_percentage(kpis.get("target_achievement"))

        if oee is not None:
            observations.append(f"OEE currently trends at {oee:.1f}%.")
        if fpy is not None:
            observations.append(f"First-pass yield sits at {fpy:.1f}%.")
        if isinstance(production, (int, float)):
            observations.append(f"Total production volume in latest run: {production:,.0f} units.")
        if target_achievement is not None:
            observations.append(
                f"Output achieved {target_achievement:.1f}% of scheduled plan during the last cycle."
            )

        claims = summary.get("claim_metrics") or {}
        total_claims = claims.get("total_claims")
        if isinstance(total_claims, (int, float)):
            observations.append(f"Claims processed: {int(total_claims)} records.")

        docs = summary.get("document_metrics") or {}
        processed = docs.get("documents_processed")
        if isinstance(processed, (int, float)):
            observations.append(f"Documents parsed by OCR/Text pipeline: {int(processed)} files.")
        return observations

    def _copilotkit_plan(self) -> Dict[str, object]:
        base_steps = [
            "Expose KPI and claim datasets via a lightweight API (FastAPI) for CopilotKit consumption.",
            "Embed CopilotKit UI components into the Streamlit dashboard using iframe or web component bridge.",
            "Design copilots for operator guidance (shift handover summary, anomaly explanations).",
        ]
        config = {
            "enabled": self.copilotkit.enabled,
            "api_base": self.copilotkit.api_base,
            "endpoint": self.copilotkit.endpoint,
            "documentation": "https://github.com/CopilotKit/CopilotKit",
            "recommended_steps": base_steps,
        }
        if not self.copilotkit.enabled:
            config["note"] = (
                "Set COPILOTKIT_API_BASE and COPILOTKIT_API_KEY in the environment to enable live copilots."
            )
        return config

    def _deep_research_plan(self) -> Dict[str, object]:
        milestones = [
            "Automate weekly deep-dives by submitting KPI deltas to Tongyi DeepResearch for root-cause narratives.",
            "Schedule claim trend analysis prompts that compare payouts against historical baselines.",
            "Feed OCR'd production logs for cross-plant benchmarking and anomaly detection.",
        ]
        config = {
            "enabled": self.deep_research.enabled,
            "api_base": self.deep_research.api_base,
            "endpoint": self.deep_research.endpoint,
            "documentation": "https://github.com/Alibaba-NLP/DeepResearch",
            "recommended_steps": milestones,
        }
        if not self.deep_research.enabled:
            config["note"] = (
                "Provide DEEPRESEARCH_API_BASE and DEEPRESEARCH_API_KEY to orchestrate autonomous research loops."
            )
        return config

    @staticmethod
    def _to_percentage(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric <= 1:
            numeric *= 100
        return numeric


__all__ = ["ResearchPlanner", "IntegrationConfig"]
