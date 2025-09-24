import importlib
import json
import os
import tempfile
from pathlib import Path
import unittest

import pandas as pd
from fastapi.testclient import TestClient


class TestInsightFactoryAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        reports_dir = Path(self.tmpdir.name) / "reports"
        os.environ["REPORTS_DIR"] = str(reports_dir)
        os.environ["INSIGHT_API_KEY"] = "secret-key"

        # Reload configuration-driven modules so they pick up the environment overrides.
        self.config = importlib.import_module("config")
        importlib.reload(self.config)
        self.api = importlib.import_module("api")
        importlib.reload(self.api)

        reports_dir = Path(self.config.REPORTS_DIR)
        reports_dir.mkdir(parents=True, exist_ok=True)

        summary_payload = {
            "kpis": {"oee": 0.92, "fpy": 0.97, "production": 1250},
            "claim_metrics": {"total_claims": 4, "total_claim_amount": 1800},
            "document_metrics": {"documents_processed": 6},
            "ai_research": {"next_actions": ["Tighten curing schedule"]},
            "performance_insights": {"forecast_notes": ["Production trending +5%"]},
            "autonomy_plan": {"immediate_actions": ["Dispatch maintenance"]},
            "system_health": {"overall_score": 82.5, "status": "excellent"},
            "run_metadata": {"duration_seconds": 42},
        }
        (reports_dir / "latest_summary.json").write_text(
            json.dumps(summary_payload),
            encoding="utf-8",
        )

        history_df = pd.DataFrame(
            [
                {"timestamp": "2024-01-01T00:00:00Z", "kpi_oee": 0.9},
                {"timestamp": "2024-01-02T00:00:00Z", "kpi_oee": 0.91},
                {"timestamp": "2024-01-03T00:00:00Z", "kpi_oee": 0.92},
            ]
        )
        history_df.to_csv(reports_dir / "run_history.csv", index=False)
        (reports_dir / "latest_summary.html").write_text("<h1>Summary</h1>", encoding="utf-8")

        self.client = TestClient(self.api.app)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        os.environ.pop("REPORTS_DIR", None)
        os.environ.pop("INSIGHT_API_KEY", None)
        import config as base_config

        importlib.reload(base_config)

    def test_requires_api_key(self) -> None:
        response = self.client.get("/api/summary")
        self.assertEqual(response.status_code, 403)

    def test_summary_endpoint(self) -> None:
        response = self.client.get(
            "/api/summary",
            headers={self.config.INSIGHT_API_KEY_HEADER: "secret-key"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["kpis"]["production"], 1250)
        self.assertIn("autonomy_plan", payload)
        self.assertEqual(payload["system_health"]["status"], "excellent")

    def test_insights_endpoint(self) -> None:
        response = self.client.get(
            "/api/insights",
            headers={self.config.INSIGHT_API_KEY_HEADER: "secret-key"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("system_health", payload)
        self.assertEqual(payload["system_health"]["status"], "excellent")

    def test_run_history_limit(self) -> None:
        response = self.client.get(
            "/api/run-history?limit=2",
            headers={self.config.INSIGHT_API_KEY_HEADER: "secret-key"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 2)
        self.assertEqual(len(body["records"]), 2)
        timestamps = [item["timestamp"] for item in body["records"]]
        self.assertEqual(
            pd.to_datetime(timestamps[-1]),
            pd.Timestamp("2024-01-03T00:00:00Z"),
        )

    def test_html_report_endpoint(self) -> None:
        response = self.client.get(
            "/api/report/html",
            headers={self.config.INSIGHT_API_KEY_HEADER: "secret-key"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Summary", response.text)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["summary_available"], "true")
        self.assertEqual(body["run_history_available"], "true")
