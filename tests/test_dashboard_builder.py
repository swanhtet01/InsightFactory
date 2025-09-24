import importlib
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest


class TestDashboardBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        reports_dir = Path(self.tmpdir.name) / "reports"
        os.environ["REPORTS_DIR"] = str(reports_dir)

        self.config = importlib.import_module("config")
        importlib.reload(self.config)
        self.dashboard_builder = importlib.import_module("helpers.dashboard_builder")
        importlib.reload(self.dashboard_builder)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        os.environ.pop("REPORTS_DIR", None)
        import config as base_config

        importlib.reload(base_config)

    def _summary_payload(self) -> dict:
        return {
            "kpis": {"oee": 0.88, "fpy": 0.93, "production": 1200},
            "claim_metrics": {"total_claims": 3, "total_claim_amount": 1500},
            "document_metrics": {"documents_processed": 5},
            "system_health": {
                "overall_score": 78.2,
                "status": "stable",
                "signals": ["Review scrap on Line 2"],
            },
            "performance_insights": {
                "alerts": ["Production dipped below target yesterday"],
                "forecast_notes": ["Throughput projected +2% next run"],
                "trend_status": "warning",
            },
            "ai_research": {
                "next_actions": ["Calibrate curing press"],
                "observations": ["Shift A trend improving"],
            },
            "autonomy_plan": {
                "immediate_actions": ["Trigger maintenance checklist"],
                "opportunities": ["Automate scrap escalation"],
            },
            "data_profile": {
                "files_profiled": 12,
                "inputs_received": 14,
                "unreadable_files": 1,
                "granularity_tags": ["daily", "per-shift"],
                "sample_files": ["plant-a/kpi.xlsx"],
                "extensions": {".xlsx": 4, ".csv": 6},
                "latest_modified": "2024-01-10T02:30:00Z",
            },
            "data_sources": {
                "total_files": 14,
                "folders": [
                    {
                        "folder_label": "Plant A",
                        "files": 7,
                        "latest_modified": "2024-01-10T02:30:00Z",
                        "contributors": ["planner@example.com"],
                    },
                    {
                        "folder_label": "Plant B",
                        "files": 7,
                        "latest_modified": "2024-01-09T18:05:00Z",
                        "contributors": ["ops@example.com"],
                    },
                ],
            },
            "run_metadata": {"started_at": "2024-01-10T03:00:00Z"},
        }

    def test_build_dashboard_payload(self) -> None:
        summary = self._summary_payload()
        summary["run_metadata"]["started_at"] = datetime.now(timezone.utc).isoformat()
        history = [
            {
                "timestamp": "2024-01-09T03:00:00Z",
                "kpi_oee": 0.86,
                "kpi_fpy": 0.92,
                "kpi_production": 1150,
                "claim_total_claims": 2,
                "claim_total_claim_amount": 1200,
                "document_documents_processed": 4,
            },
            {
                "timestamp": "2024-01-10T03:00:00Z",
                "kpi_oee": 0.88,
                "kpi_fpy": 0.93,
                "kpi_production": 1200,
                "claim_total_claims": 3,
                "claim_total_claim_amount": 1500,
                "document_documents_processed": 5,
            },
        ]

        payload = self.dashboard_builder.build_dashboard_payload(summary, history)

        hero_labels = [metric["label"] for metric in payload["hero_metrics"]]
        self.assertIn("Overall Equipment Effectiveness", hero_labels)
        oee_metric = payload["hero_metrics"][0]
        self.assertTrue(oee_metric["value"].endswith("%"))
        self.assertEqual(oee_metric["delta"], "+2.0pp")

        next_actions = payload["next_actions"]
        self.assertIn("Calibrate curing press", next_actions)
        self.assertIn("Automate scrap escalation", next_actions)

        trends = {series["label"]: series for series in payload["trend_series"]}
        self.assertIn("Overall Equipment Effectiveness", trends)
        oee_points = trends["Overall Equipment Effectiveness"]["points"]
        self.assertAlmostEqual(oee_points[0]["value"], 86.0)
        self.assertAlmostEqual(oee_points[-1]["value"], 88.0)

        intake = payload["data_intake"]
        self.assertEqual(intake["files_profiled"], 12)
        self.assertIn("daily", intake["granularity_tags"])

        freshness = payload["freshness"]
        self.assertEqual(freshness["status"], "fresh")
        self.assertIn("Pipeline executed", freshness["message"])

    def test_freshness_categories(self) -> None:
        summary = self._summary_payload()
        now = datetime.now(timezone.utc)

        for minutes, expected in ((30, "fresh"), (120, "stale"), (480, "overdue")):
            summary["run_metadata"]["started_at"] = (now - timedelta(minutes=minutes)).isoformat()
            payload = self.dashboard_builder.build_dashboard_payload(summary, [])
            self.assertEqual(payload["freshness"]["status"], expected)

    def test_write_dashboard_persists_file(self) -> None:
        summary = self._summary_payload()
        history = [
            {"timestamp": "2024-01-10T03:00:00Z", "kpi_oee": 0.88},
        ]

        payload = self.dashboard_builder.write_dashboard(summary, history)
        dashboard_path = Path(self.config.REPORTS_DIR) / self.dashboard_builder.DASHBOARD_FILENAME
        self.assertTrue(dashboard_path.exists())
        stored = json.loads(dashboard_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["hero_metrics"], payload["hero_metrics"])

