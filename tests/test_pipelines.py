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
            "oee,fpy,quantity,target,a_grade,b_grade,scrap\n0.8,0.9,100,120,90,10,5\n",
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
        self.assertEqual(kpi_df.loc[0, "production"], 100)
        self.assertAlmostEqual(kpi_df.loc[0, "target_achievement"], 100 / 120 * 100)

    def test_full_pipeline(self) -> None:
        txt = Path("sample.txt")
        img = Path("sample.png")
        claim = Path("claim.csv")
        kpi = Path("data.csv")

        txt.write_text("Hello TXT", encoding="utf-8")
        create_png(img, "Hello Image")
        claim.write_text("amount\n10\n20\n", encoding="utf-8")
        kpi.write_text(
            "oee,fpy,quantity,target,a_grade,b_grade,scrap\n0.8,0.9,100,120,90,10,5\n",
            encoding="utf-8",
        )

        run_full_pipeline(collect_files(["."]))

        summary = Path("reports/latest_summary.json")
        self.assertTrue(summary.exists())
        data = json.loads(summary.read_text(encoding="utf-8"))
        self.assertIn("kpis", data)
        self.assertIn("claim_metrics", data)
        self.assertIn("document_metrics", data)

    def test_collect_files(self) -> None:
        txt = Path("sample.txt")
        img_dir = Path("sub")
        img_dir.mkdir()
        img = img_dir / "sample.png"

        txt.write_text("Hello", encoding="utf-8")
        create_png(img, "Hello")

        files = collect_files(["."])
        self.assertIn(str(txt), files)
        self.assertIn(str(img), files)



if __name__ == "__main__":
    unittest.main()

