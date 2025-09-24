"""Extract text from synced documents for downstream analysis."""
from typing import List
import os
import pandas as pd
try:
    from pdfminer.high_level import extract_text
except Exception:  # pragma: no cover - dependency optional
    extract_text = None
from PIL import Image
import pytesseract

from config import REPORTS_DIR


def _extract_text_from_file(path: str) -> str:
    if path.lower().endswith('.pdf'):
        if extract_text is None:
            print("pdfminer not installed; cannot parse PDF")
            return ""
        try:
            return extract_text(path)
        except Exception as e:
            print(f"Failed to parse PDF {path}: {e}")
            return ""
    if path.lower().endswith(('.png', '.jpg', '.jpeg')):
        try:
            return pytesseract.image_to_string(Image.open(path))
        except Exception as e:
            print(f"Failed to OCR image {path}: {e}")
            return ""
    if path.lower().endswith('.txt'):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Failed to read text file {path}: {e}")
            return ""
    return ""


def process_documents(files: List[str]) -> dict:
    docs = [f for f in files if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.txt'))]
    if not docs:
        return {}
    extracts = []
    metrics = []
    for path in docs:
        text = _extract_text_from_file(path)
        if text:
            basename = os.path.basename(path)
            extracts.append(f"== {basename} ==\n{text.strip()}\n")
            metrics.append({"file": basename, "word_count": len(text.split())})
    if extracts:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        docs_path = REPORTS_DIR / 'latest_docs.txt'
        metrics_path = REPORTS_DIR / 'latest_doc_metrics.csv'
        docs_path.write_text('\n'.join(extracts), encoding='utf-8')
        pd.DataFrame(metrics).to_csv(metrics_path, index=False)
        print(f'Saved document extracts to {docs_path}')
    return {"documents_processed": len(metrics)}
