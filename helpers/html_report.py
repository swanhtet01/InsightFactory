"""Generate a simple HTML report from pipeline summary data."""
from typing import Dict, Any, Iterable
import os
from pathlib import Path
import pandas as pd


def _format_value(value: Any, unit: str) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if unit == "%":
        return f"{float(value):.1f}%"
    if unit == "currency":
        return f"${float(value):,.2f}"
    if isinstance(value, (int, float)):
        return f"{float(value):.1f}"
    return str(value)


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

    system_health = summary.get("system_health") or {}
    if system_health:
        overall = system_health.get("overall_score")
        status = system_health.get("status")
        if overall is not None or status:
            sections.append("<h2>Health Scorecard</h2>")
            rows = []
            if overall is not None:
                rows.append({"Metric": "Overall score", "Value": f"{float(overall):.1f}"})
            if status:
                rows.append({"Metric": "Status", "Value": status.replace("_", " ").title()})
            for component in system_health.get("components", []):
                rows.append(
                    {
                        "Metric": component.get("name"),
                        "Value": f"{float(component.get('score', 0)):.1f}",
                        "Status": component.get("status", ""),
                        "Detail": component.get("detail", ""),
                    }
                )
            if rows:
                sections.append(pd.DataFrame(rows).to_html(index=False))
            signals = system_health.get("signals") or []
            if signals:
                sections.append("<h3>Attention Items</h3>")
                sections.append("<ul>")
                for signal in signals:
                    sections.append(f"<li>{signal}</li>")
                sections.append("</ul>")

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

    data_profile = summary.get("data_profile") or {}
    if data_profile:
        sections.append("<h2>Data Intake Profile</h2>")
        overview_rows = []
        overview_mapping = [
            ("Inputs received", data_profile.get("inputs_received")),
            ("Unique files", data_profile.get("total_files")),
            ("Files profiled", data_profile.get("files_profiled")),
            ("Unreadable files", data_profile.get("unreadable_files")),
            (
                "Total volume (MB)",
                f"{data_profile.get('total_bytes', 0) / (1024 ** 2):.2f}",
            ),
            (
                "Average file size (KB)",
                f"{data_profile.get('average_bytes', 0) / 1024:.2f}",
            ),
            ("Earliest modified", data_profile.get("earliest_modified")),
            ("Latest modified", data_profile.get("latest_modified")),
        ]
        for label, value in overview_mapping:
            if value not in (None, ""):
                overview_rows.append({"Metric": label, "Value": value})
        if overview_rows:
            sections.append(pd.DataFrame(overview_rows).to_html(index=False))

        extensions = data_profile.get("extensions") or {}
        if extensions:
            ext_rows = [
                {"Extension": ext, "Files": count}
                for ext, count in sorted(extensions.items(), key=lambda kv: (-kv[1], kv[0]))
            ]
            sections.append("<h3>Files by Type</h3>")
            sections.append(pd.DataFrame(ext_rows).to_html(index=False))

        def _render_list(items: Iterable[str], title: str) -> None:
            seq = [item for item in items if item]
            if not seq:
                return
            sections.append(f"<h3>{title}</h3>")
            sections.append("<ul>")
            for item in seq:
                sections.append(f"<li>{item}</li>")
            sections.append("</ul>")

        _render_list(data_profile.get("sample_files", []), "Sample Files")
        _render_list(
            data_profile.get("granularity_tags", []),
            "Detected Granularity Tags",
        )

    data_sources = summary.get("data_sources") or {}
    folders = data_sources.get("folders") if isinstance(data_sources, dict) else None
    if folders:
        sections.append("<h2>Data Sources</h2>")
        folder_rows = []
        for folder in folders:
            folder_rows.append(
                {
                    "Folder": folder.get("folder_label") or folder.get("folder_id"),
                    "Files": folder.get("files", 0),
                    "Latest Modified": folder.get("latest_modified"),
                    "Earliest Modified": folder.get("earliest_modified"),
                    "Contributors": ", ".join(folder.get("contributors", [])),
                }
            )
        if folder_rows:
            sections.append(pd.DataFrame(folder_rows).to_html(index=False))

        entries = data_sources.get("entries", [])
        if entries:
            sections.append("<h3>Latest Files</h3>")
            entry_df = pd.DataFrame(entries)
            if not entry_df.empty:
                if "modified_time" in entry_df.columns:
                    entry_df = entry_df.sort_values("modified_time", ascending=False)
                sections.append(
                    entry_df[
                        [
                            col
                            for col in [
                                "name",
                                "folder_label",
                                "mime_type",
                                "modified_time",
                                "local_path",
                            ]
                            if col in entry_df.columns
                        ]
                    ]
                    .head(10)
                    .to_html(index=False)
                )

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

    run_metadata = summary.get("run_metadata") or {}
    if run_metadata:
        sections.append("<h2>Run Metadata</h2>")
        metadata_rows = []
        for key, label in (
            ("started_at", "Started"),
            ("duration_seconds", "Duration (s)"),
            ("files_collected", "Files Collected"),
            ("files_profiled", "Files Profiled"),
        ):
            value = run_metadata.get(key)
            if value in (None, ""):
                continue
            if isinstance(value, float):
                value = f"{value:.3f}" if key == "duration_seconds" else f"{value:.1f}"
            metadata_rows.append({"Metric": label, "Value": value})
        reports_written = run_metadata.get("reports_written") or []
        if reports_written:
            metadata_rows.append(
                {
                    "Metric": "Reports Written",
                    "Value": ", ".join(reports_written),
                }
            )
        if metadata_rows:
            sections.append(pd.DataFrame(metadata_rows).to_html(index=False))

    performance = summary.get("performance_insights") or {}
    if performance:
        sections.append("<h2>Performance Insights</h2>")
        trends = performance.get("trends") or []
        if trends:
            trend_rows = []
            for entry in trends:
                unit = entry.get("unit", "")
                trend_rows.append(
                    {
                        "Metric": entry.get("metric"),
                        "Status": entry.get("status"),
                        "Current": _format_value(entry.get("current"), unit),
                        "Previous": _format_value(entry.get("previous"), unit),
                        "Δ": _format_value(entry.get("change"), unit),
                        "Δ per Run": _format_value(entry.get("trend_per_run"), unit),
                        "Window": entry.get("window"),
                    }
                )
            sections.append(pd.DataFrame(trend_rows).to_html(index=False))

        for key, label, css in (
            ("alerts", "Alerts", "<ul class='alerts'>"),
            ("opportunities", "Opportunities", "<ul class='opportunities'>"),
            ("volatility", "Volatility", "<ul class='volatility'>"),
        ):
            messages = performance.get(key) or []
            if messages:
                sections.append(f"<h3>{label}</h3>")
                sections.append(css)
                for msg in messages:
                    sections.append(f"<li>{msg}</li>")
                sections.append("</ul>")

        notes = performance.get("notes") or []
        if notes:
            sections.append("<h3>Notes</h3>")
            sections.append("<ul class='notes'>")
            for note in notes:
                sections.append(f"<li>{note}</li>")
            sections.append("</ul>")

        forecast_notes = performance.get("forecast_notes") or []
        if forecast_notes:
            sections.append("<h3>Forecast Highlights</h3>")
            sections.append("<ul class='forecast-notes'>")
            for note in forecast_notes:
                sections.append(f"<li>{note}</li>")
            sections.append("</ul>")

    autonomy = summary.get("autonomy_plan") or {}
    if autonomy:
        sections.append("<h2>Autonomous Operations Plan</h2>")
        if autonomy.get("immediate_actions"):
            sections.append("<h3>Immediate Actions</h3>")
            sections.append("<ul>")
            for item in autonomy["immediate_actions"]:
                sections.append(f"<li>{item}</li>")
            sections.append("</ul>")

        if autonomy.get("automation_opportunities"):
            sections.append("<h3>Automation Opportunities</h3>")
            sections.append("<ul>")
            for item in autonomy["automation_opportunities"]:
                sections.append(f"<li>{item}</li>")
            sections.append("</ul>")

        if autonomy.get("monitoring"):
            sections.append("<h3>Monitoring Watchlist</h3>")
            sections.append("<ul>")
            for item in autonomy["monitoring"]:
                sections.append(f"<li>{item}</li>")
            sections.append("</ul>")

        agents = autonomy.get("agents") or []
        if agents:
            sections.append("<h3>Agent Roster</h3>")
            agent_rows = []
            for agent in agents:
                agent_rows.append(
                    {
                        "Agent": agent.get("name"),
                        "Status": agent.get("status"),
                        "Description": agent.get("description"),
                        "Triggers": ", ".join(agent.get("triggers", [])),
                        "Next Steps": ", ".join(agent.get("next_steps", [])),
                    }
                )
            sections.append(pd.DataFrame(agent_rows).to_html(index=False))

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
