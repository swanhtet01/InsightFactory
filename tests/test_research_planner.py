import unittest
from helpers.integration_clients import IntegrationResult
from helpers.research_planner import ResearchPlanner, IntegrationConfig


class ResearchPlannerTest(unittest.TestCase):
    def test_generate_insights_without_credentials(self) -> None:
        planner = ResearchPlanner()
        summary = {
            "kpis": {"oee": 0.8, "fpy": 0.92, "production": 1200, "target_achievement": 95},
            "claim_metrics": {"total_claims": 3, "total_claim_amount": 1500},
            "document_metrics": {"documents_processed": 2},
        }
        insights = planner.generate_insights(summary)
        self.assertIn("next_actions", insights)
        self.assertTrue(insights["next_actions"])
        self.assertIn("tooling", insights)
        self.assertFalse(insights["tooling"]["copilotkit"]["enabled"])
        self.assertFalse(insights["tooling"]["deep_research"]["enabled"])
        self.assertIn("integrations", insights)
        self.assertEqual(insights["integrations"]["copilotkit"]["status"], "disabled")
        self.assertEqual(insights["integrations"]["deep_research"]["status"], "disabled")
        self.assertIn("metadata", insights)

    def test_generate_insights_with_credentials(self) -> None:
        class DummyClient:
            def __init__(self, status: str) -> None:
                self._status = status

            @property
            def enabled(self) -> bool:
                return True

            def request_brief(self, summary):
                return IntegrationResult(status=self._status, data={"summary_keys": list(summary.keys())})

            def request_research(self, summary):
                return IntegrationResult(status=self._status, data={"summary_keys": list(summary.keys())})

        copilot_config = IntegrationConfig(name="CopilotKit", api_base="https://copilot", api_key="demo")
        deep_config = IntegrationConfig(name="DeepResearch", api_base="https://deep", api_key="demo")
        dummy_client = DummyClient(status="ok")
        planner = ResearchPlanner(
            copilotkit=copilot_config,
            deep_research=deep_config,
            copilotkit_client=dummy_client,
            deep_research_client=dummy_client,
        )
        summary = {"kpis": {}, "claim_metrics": {}, "document_metrics": {}}
        insights = planner.generate_insights(summary)
        self.assertTrue(insights["tooling"]["copilotkit"]["enabled"])
        self.assertTrue(insights["tooling"]["deep_research"]["enabled"])
        self.assertIn("generated_at", insights["metadata"])
        self.assertEqual(insights["integrations"]["copilotkit"]["status"], "ok")
        self.assertEqual(insights["integrations"]["deep_research"]["status"], "ok")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
