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
        os.makedirs('reports', exist_ok=True)
        with open('reports/latest_docs.txt', 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(extracts))
        pd.DataFrame(metrics).to_csv('reports/latest_doc_metrics.csv', index=False)
        print('Saved document extracts to reports/latest_docs.txt')
    return {"documents_processed": len(metrics)}
