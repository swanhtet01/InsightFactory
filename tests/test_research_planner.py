import unittest
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
        self.assertIn("metadata", insights)

    def test_generate_insights_with_credentials(self) -> None:
        planner = ResearchPlanner(
            copilotkit=IntegrationConfig(name="CopilotKit", api_base="https://copilot", api_key="demo"),
            deep_research=IntegrationConfig(name="DeepResearch", api_base="https://deep", api_key="demo"),
        )
        summary = {"kpis": {}, "claim_metrics": {}, "document_metrics": {}}
        insights = planner.generate_insights(summary)
        self.assertTrue(insights["tooling"]["copilotkit"]["enabled"])
        self.assertTrue(insights["tooling"]["deep_research"]["enabled"])
        self.assertIn("generated_at", insights["metadata"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
