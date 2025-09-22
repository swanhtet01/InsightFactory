import unittest
from unittest import mock

from requests import exceptions

from helpers.integration_clients import (
    CopilotKitClient,
    IntegrationResult,
    TongyiDeepResearchClient,
)


class IntegrationClientsTest(unittest.TestCase):
    def test_copilotkit_success(self) -> None:
        session = mock.Mock()
        response = mock.Mock()
        response.json.return_value = {"plan": ["step1"]}
        response.raise_for_status.return_value = None
        session.post.return_value = response

        client = CopilotKitClient(
            api_base="https://example.com",
            api_key="token",
            endpoint="/insights",
            session=session,
        )
        result = client.request_brief({"kpis": {}})
        self.assertIsInstance(result, IntegrationResult)
        self.assertEqual(result.status, "ok")
        session.post.assert_called_once()
        self.assertEqual(result.data, {"plan": ["step1"]})

    def test_deep_research_error(self) -> None:
        session = mock.Mock()
        session.post.side_effect = exceptions.RequestException("boom")

        client = TongyiDeepResearchClient(
            api_base="https://example.com",
            endpoint="/research",
            session=session,
        )
        result = client.request_research({"kpis": {}})
        self.assertEqual(result.status, "error")
        self.assertIn("boom", result.error)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
