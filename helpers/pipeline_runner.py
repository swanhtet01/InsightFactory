"""Unified pipeline runner for syncing, KPI, claim, and document processing."""
from typing import List, Dict

from helpers.live_kpi_pipeline import compute_kpis_for_files
from helpers.claims_pipeline import compute_claim_metrics
from helpers.document_processor import process_documents


def run_full_pipeline(files: List[str]) -> Dict[str, Dict]:
    """Run all available processing pipelines on the given files.

    Parameters
    ----------
    files: List[str]
        Paths to files that should be analyzed.

    Returns
    -------
    Dict[str, Dict]
        A dictionary containing results from each pipeline for convenience.
    """
    results: Dict[str, Dict] = {}
    results["kpis"] = compute_kpis_for_files(files)
    results["claim_metrics"] = compute_claim_metrics(files)
    results["document_metrics"] = process_documents(files)
    return results


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    import sys

    run_full_pipeline(sys.argv[1:])
