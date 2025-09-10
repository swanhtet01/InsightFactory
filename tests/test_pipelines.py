import os
import shutil
import tempfile
from pathlib import Path
import unittest

import pandas as pd

from helpers.document_processor import process_documents, extract_text as pdf_extract_text
from helpers.claims_pipeline import compute_claim_metrics
from helpers.live_kpi_pipeline import compute_kpis_for_files


PDF_BYTES = b"""%PDF-1.1\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Type /Font /Subtype /Type1 /Name /F1 /BaseFont /Helvetica >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT /F1 18 Tf 50 150 Td (Hello PDF) Tj ET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000063 00000 n \n0000000116 00000 n \n0000000277 00000 n \n0000000346 00000 n \ntrailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n423\n%%EOF"""

def create_pdf(path: Path) -> None:
    with open(path, "wb") as fh:
        fh.write(PDF_BYTES)

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
        pdf = Path("sample.pdf")
        txt = Path("sample.txt")
        img = Path("sample.png")
        create_pdf(pdf)
        txt.write_text("Hello TXT", encoding="utf-8")
        create_png(img, "Hello Image")

        process_documents([str(pdf), str(txt), str(img)])
        out = Path("reports/latest_docs.txt")
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        metrics_path = Path("reports/latest_doc_metrics.csv")
        self.assertTrue(metrics_path.exists())
        metrics_df = pd.read_csv(metrics_path)

        if pdf_extract_text is not None:
            self.assertIn("Hello PDF", content)
            pdf_wc = metrics_df.loc[metrics_df["file"] == "sample.pdf", "word_count"].iloc[0]
            self.assertEqual(pdf_wc, 2)
        else:
            self.assertNotIn("Hello PDF", content)
            self.assertFalse((metrics_df["file"] == "sample.pdf").any())

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


if __name__ == "__main__":
    unittest.main()
