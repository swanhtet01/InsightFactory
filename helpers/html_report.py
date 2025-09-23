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

    ai_research = summary.get("ai_research") or {}
    if ai_research:
        sections.append("<h2>AI Research Insights</h2>")
        observations = ai_research.get("observations") or []
        if observations:
            sections.append("<h3>Observations</h3>")
            sections.append("<ul>")
            for obs in observations:
                sections.append(f"<li>{obs}</li>")
            sections.append("</ul>")

        actions = ai_research.get("next_actions") or []
        if actions:
            sections.append("<h3>Next Actions</h3>")
            sections.append("<ul>")
            for action in actions:
                sections.append(f"<li>{action}</li>")
            sections.append("</ul>")

        integrations = ai_research.get("integrations") or {}
        if integrations:
            sections.append("<h3>Integration Status</h3>")
            rows = []
            for name, info in integrations.items():
                rows.append({
                    "Integration": name.replace("_", " ").title(),
                    "Status": info.get("status"),
                    "Error": info.get("error"),
                })
            sections.append(pd.DataFrame(rows).to_html(index=False))

    history_path = Path("reports/run_history.csv")
    if history_path.exists():
        try:
            history_df = pd.read_csv(history_path)
        except Exception:
            history_df = None
        if history_df is not None and not history_df.empty:
            sections.append("<h2>Run History</h2>")
            tail = history_df.tail(10).copy()
            if "timestamp" in tail.columns:
                parsed = pd.to_datetime(tail["timestamp"], errors="coerce")
                formatted = parsed.dt.strftime("%Y-%m-%d %H:%M:%S%z")
                tail["timestamp"] = formatted.fillna(tail["timestamp"].astype(str))
            sections.append(tail.to_html(index=False))

    sections.extend(["</body>", "</html>"])
    output.write_text("\n".join(sections), encoding="utf-8")
