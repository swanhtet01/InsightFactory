"""Unified pipeline runner for syncing, KPI, claim, and document processing."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List
import json
import os
import time

from config import REPORTS_DIR
from helpers.claims_pipeline import compute_claim_metrics
from helpers.document_processor import process_documents
from helpers.live_kpi_pipeline import compute_kpis_for_files
from helpers.html_report import write_html_report
from helpers.research_planner import ResearchPlanner
from helpers.run_history import record_run, flatten_summary
from helpers.performance_analyzer import generate_performance_insights
from helpers.autonomy_orchestrator import generate_autonomy_plan
from helpers.data_profiler import profile_files
from helpers.source_registry import load_latest_sync
from helpers.health_evaluator import evaluate_system_health
from helpers.serialization import to_serializable


EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "reports",
    "venv",
    ".venv",
}

EXCLUDED_DIR_NAMES.add(REPORTS_DIR.name.lower())

EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp"}


def collect_files(paths: Iterable[str]) -> List[str]:
    """Expand files and directories into a flat list of file paths."""

    files: List[str] = []
    seen = set()
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for root, dirs, filenames in os.walk(path):
                dirs[:] = sorted(
                    d for d in dirs if d.lower() not in EXCLUDED_DIR_NAMES
                )
                for filename in sorted(filenames):
                    candidate = Path(root) / filename
                    if candidate.suffix.lower() in EXCLUDED_SUFFIXES:
                        continue
                    resolved = str(candidate.resolve())
                    if resolved in seen:
                        continue
                    seen.add(resolved)
                    files.append(str(candidate))
        elif path.is_file():
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(str(path))
    return files


def run_full_pipeline(files: List[str]) -> Dict[str, Dict]:
    """Run all available processing pipelines on the given files."""

    started_at = datetime.now(timezone.utc)
    started_clock = time.perf_counter()
    results: Dict[str, Dict] = {}

    data_profile = profile_files(files)
    source_snapshot = load_latest_sync()
    if data_profile:
        results["data_profile"] = data_profile
    if source_snapshot:
        results["data_sources"] = source_snapshot

    results["kpis"] = compute_kpis_for_files(files)
    results["claim_metrics"] = compute_claim_metrics(files)
    results["document_metrics"] = process_documents(files)
    planner = ResearchPlanner.from_env()
    results["ai_research"] = planner.generate_insights(results)

    results["system_health"] = evaluate_system_health(results)

    if any(results.values()):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        outputs: List[str] = []
        if results.get("kpis"):
            outputs.append(str(REPORTS_DIR / "latest_kpis.csv"))
        if results.get("claim_metrics"):
            outputs.append(str(REPORTS_DIR / "latest_claim_metrics.csv"))
        if results.get("document_metrics"):
            outputs.append(str(REPORTS_DIR / "latest_docs.txt"))

        duration = time.perf_counter() - started_clock
        results["run_metadata"] = {
            "started_at": started_at.isoformat(),
            "duration_seconds": round(duration, 3),
            "files_collected": len(files),
            "files_profiled": data_profile.get("files_profiled", 0) if data_profile else 0,
            "reports_written": [],
        }

        health_status = results.get("system_health", {}).get("status")
        if health_status:
            results["run_metadata"]["health_status"] = health_status

        if source_snapshot:
            results["run_metadata"]["sources_tracked"] = len(
                source_snapshot.get("folders", [])
            )

        outputs.append(str(REPORTS_DIR / "run_history.csv"))
        outputs.extend(
            [
                str(REPORTS_DIR / "latest_summary.json"),
                str(REPORTS_DIR / "latest_summary.html"),
            ]
        )
        pending_row = flatten_summary(results)
        results["performance_insights"] = generate_performance_insights(
            results, pending_row=pending_row
        )
        results["autonomy_plan"] = generate_autonomy_plan(results)
        results["run_metadata"]["reports_written"] = sorted(set(outputs))
        record_run(results)
        summary_path = REPORTS_DIR / "latest_summary.json"
        with summary_path.open("w", encoding="utf-8") as fh:
            json.dump(to_serializable(results), fh, indent=2)
        write_html_report(results)
    return results


def main(argv: Iterable[str]) -> None:  # pragma: no cover - CLI entrypoint
    """Command line interface for the pipeline runner."""

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths", nargs="+", help="Files or directories to include in the run"
    )
    args = parser.parse_args(list(argv))
    files = collect_files(args.paths)
    run_full_pipeline(files)


if __name__ == "__main__":  # pragma: no cover
    import sys

    main(sys.argv[1:])
