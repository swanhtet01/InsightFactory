import os
import shutil
import tempfile
from pathlib import Path
import unittest
import json

import pandas as pd

from helpers.document_processor import process_documents
from helpers.claims_pipeline import compute_claim_metrics
from helpers.live_kpi_pipeline import compute_kpis_for_files
from helpers.pipeline_runner import run_full_pipeline, collect_files
from helpers.source_registry import record_sync_snapshot
from helpers.performance_analyzer import generate_performance_insights


def create_png(path: Path, text: str) -> None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (200, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill=(0, 0, 0))
    img.save(path)


class TestPipelines(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self) -> None:
        os.chdir(self.repo_cwd)
        shutil.rmtree(self.tmpdir)

    def test_document_processor(self) -> None:
        txt = Path("sample.txt")
        img = Path("sample.png")
        txt.write_text("Hello TXT", encoding="utf-8")
        create_png(img, "Hello Image")

        process_documents([str(txt), str(img)])
        out = Path("reports/latest_docs.txt")
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        metrics_path = Path("reports/latest_doc_metrics.csv")
        self.assertTrue(metrics_path.exists())
        metrics_df = pd.read_csv(metrics_path)

        self.assertIn("Hello TXT", content)
        txt_wc = metrics_df.loc[metrics_df["file"] == "sample.txt", "word_count"].iloc[0]
        self.assertEqual(txt_wc, 2)

        if shutil.which("tesseract"):
            self.assertIn("Hello Image", content)

    def test_claims_and_kpi_pipelines(self) -> None:
        claim = Path("claim.csv")
        claim.write_text("amount\n10\n20\n", encoding="utf-8")
        kpi = Path("data.csv")
        kpi.write_text(
            (
                "available_time,operating_time,ideal_cycle_time,total_pieces,good_pieces,"
                "quantity,target,a_grade,b_grade,scrap\n"
                "480,450,1,400,380,400,420,380,20,20\n"
            ),
            encoding="utf-8",
        )

        compute_claim_metrics([str(claim)])
        compute_kpis_for_files([str(kpi)])

        claim_out = Path("reports/latest_claim_metrics.csv")
        kpi_out = Path("reports/latest_kpis.csv")
        self.assertTrue(claim_out.exists())
        self.assertTrue(kpi_out.exists())

        claim_df = pd.read_csv(claim_out)
        self.assertEqual(claim_df.loc[0, "total_claims"], 2)
        self.assertEqual(claim_df.loc[0, "total_claim_amount"], 30)

        kpi_df = pd.read_csv(kpi_out)
        self.assertEqual(kpi_df.loc[0, "production"], 400)
        self.assertAlmostEqual(kpi_df.loc[0, "target_achievement"], 400 / 420 * 100)
        self.assertAlmostEqual(kpi_df.loc[0, "oee"], 0.791666, places=5)
        self.assertAlmostEqual(kpi_df.loc[0, "fpy"], 0.95, places=5)

    def test_full_pipeline(self) -> None:
        txt = Path("sample.txt")
        img = Path("sample.png")
        claim = Path("claim.csv")
        kpi = Path("data.csv")

        txt.write_text("Hello TXT", encoding="utf-8")
        create_png(img, "Hello Image")
        claim.write_text("amount\n10\n20\n", encoding="utf-8")
        kpi.write_text(
            (
                "available_time,operating_time,ideal_cycle_time,total_pieces,good_pieces,"
                "quantity,target,a_grade,b_grade,scrap\n"
                "480,450,1,400,380,400,420,380,20,20\n"
            ),
            encoding="utf-8",
        )

        record_sync_snapshot(
            [
                {
                    "folder_id": "plant-a",
                    "folder_label": "Plant A",
                    "folder_slug": "plant_a",
                    "file_id": "file-1",
                    "name": "sample.txt",
                    "mime_type": "text/plain",
                    "local_path": str(txt.resolve()),
                    "modified_time": "2024-01-01T00:00:00Z",
                    "owners": [{"emailAddress": "ops@example.com"}],
                    "last_modified_by": "ops@example.com",
                },
                {
                    "folder_id": "plant-b",
                    "folder_label": "Plant B",
                    "folder_slug": "plant_b",
                    "file_id": "file-2",
                    "name": "claim.csv",
                    "mime_type": "text/csv",
                    "local_path": str(claim.resolve()),
                    "modified_time": "2024-01-02T00:00:00Z",
                    "owners": [{"displayName": "Planner"}],
                    "last_modified_by": "planner@example.com",
                },
            ]
        )

        run_full_pipeline(collect_files(["."]))

        summary = Path("reports/latest_summary.json")
        self.assertTrue(summary.exists())
        data = json.loads(summary.read_text(encoding="utf-8"))
        self.assertIn("kpis", data)
        self.assertIn("claim_metrics", data)
        self.assertIn("document_metrics", data)
        self.assertIn("data_profile", data)
        self.assertIn("run_metadata", data)
        self.assertIn("data_sources", data)
        self.assertIn("ai_research", data)
        self.assertIn("performance_insights", data)
        self.assertIn("oee", data["kpis"])

        data_profile = data["data_profile"]
        self.assertGreaterEqual(data_profile.get("files_profiled", 0), 2)
        self.assertIn("txt", data_profile.get("extensions", {}))
        self.assertGreaterEqual(
            data_profile.get("inputs_received", 0), data_profile.get("total_files", 0)
        )

        metadata = data["run_metadata"]
        self.assertIn("duration_seconds", metadata)
        self.assertIn("reports/latest_summary.html", metadata["reports_written"])
        self.assertEqual(metadata.get("sources_tracked"), 2)

        sources = data["data_sources"]
        self.assertEqual(sources.get("total_files"), 2)
        folder_labels = {folder.get("folder_label") for folder in sources.get("folders", [])}
        self.assertSetEqual(folder_labels, {"Plant A", "Plant B"})

        research = data["ai_research"]
        self.assertIn("next_actions", research)
        self.assertTrue(research["next_actions"])
        self.assertIn("tooling", research)
        self.assertIn("copilotkit", research["tooling"])
        self.assertIn("deep_research", research["tooling"])
        self.assertIn("integrations", research)
        self.assertEqual(research["integrations"]["copilotkit"]["status"], "disabled")

        html = Path("reports/latest_summary.html")
        self.assertTrue(html.exists())
        html_content = html.read_text(encoding="utf-8")
        self.assertIn("Pipeline Summary", html_content)
        self.assertIn("Run History", html_content)
        self.assertIn("Data Intake Profile", html_content)
        self.assertIn("Run Metadata", html_content)

        history = Path("reports/run_history.csv")
        self.assertTrue(history.exists())
        history_df = pd.read_csv(history)
        self.assertGreaterEqual(len(history_df), 1)
        self.assertIn("kpi_oee", history_df.columns)
        self.assertIn("data_profile_inputs_received", history_df.columns)
        self.assertIn("data_profile_total_files", history_df.columns)
        self.assertIn("run_metadata_duration_seconds", history_df.columns)

        initial_rows = len(history_df)
        run_full_pipeline(collect_files(["."]))
        updated_history = pd.read_csv(history)
        self.assertGreater(len(updated_history), initial_rows)

        updated_summary = json.loads(summary.read_text(encoding="utf-8"))
        insights = updated_summary.get("performance_insights", {})
        self.assertTrue(isinstance(insights, dict))
        self.assertIn("trends", insights)
        self.assertGreaterEqual(len(insights.get("trends", [])), 1)

    def test_collect_files(self) -> None:
        txt = Path("sample.txt")
        img_dir = Path("sub")
        img_dir.mkdir()
        img = img_dir / "sample.png"
        reports_dir = Path("reports")
        reports_dir.mkdir()
        generated = reports_dir / "latest_kpis.csv"
        generated.write_text("value\n1\n", encoding="utf-8")

        txt.write_text("Hello", encoding="utf-8")
        create_png(img, "Hello")

        files = collect_files(["."])
        self.assertIn(str(txt), files)
        self.assertIn(str(img), files)
        self.assertNotIn(str(generated), files)

    def test_performance_insights_generation(self) -> None:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        history = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=4, freq="D"),
                "kpi_oee": [0.75, 0.78, 0.82, 0.86],
                "kpi_production": [100, 105, 110, 130],
                "claim_total_claims": [12, 11, 9, 7],
                "document_documents_processed": [4, 5, 6, 8],
            }
        )
        history.to_csv(reports_dir / "run_history.csv", index=False)

        insights = generate_performance_insights({}, history_path=reports_dir / "run_history.csv")
        self.assertIn("trends", insights)
        self.assertTrue(any(t["metric"] == "Overall Equipment Effectiveness" for t in insights["trends"]))
        self.assertIn("alerts", insights)
        self.assertIn("opportunities", insights)



if __name__ == "__main__":
    unittest.main()

