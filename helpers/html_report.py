"""Generate a simple HTML report from pipeline summary data."""
from typing import Dict
import os
from pathlib import Path
import pandas as pd


def write_html_report(summary: Dict, path: str = "reports/latest_summary.html") -> None:
    """Write an HTML report for the provided summary metrics.

    Parameters
    ----------
    summary:
        Dictionary with keys ``kpis``, ``claim_metrics`` and ``document_metrics``.
    path:
        Output HTML file path.
    """
    output = Path(path)
    os.makedirs(output.parent, exist_ok=True)

    sections = ["<html>", "<body>", "<h1>Pipeline Summary</h1>"]

    if summary.get("kpis"):
        sections.append("<h2>KPIs</h2>")
        sections.append(pd.DataFrame([summary["kpis"]]).to_html(index=False))

    if summary.get("claim_metrics"):
        sections.append("<h2>Claim Metrics</h2>")
        sections.append(pd.DataFrame([summary["claim_metrics"]]).to_html(index=False))

    doc_metrics = summary.get("document_metrics")
    if doc_metrics:
        sections.append("<h2>Document Metrics</h2>")
        if isinstance(doc_metrics, list):
            sections.append(pd.DataFrame(doc_metrics).to_html(index=False))
        else:
            sections.append(pd.DataFrame([doc_metrics]).to_html(index=False))

    sections.extend(["</body>", "</html>"])
    output.write_text("\n".join(sections), encoding="utf-8")
