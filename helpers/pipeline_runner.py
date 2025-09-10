"""Unified pipeline runner for syncing, KPI, claim, and document processing."""
from pathlib import Path
from typing import Dict, Iterable, List

from helpers.claims_pipeline import compute_claim_metrics
from helpers.document_processor import process_documents
from helpers.live_kpi_pipeline import compute_kpis_for_files


def collect_files(paths: Iterable[str]) -> List[str]:
    """Expand files and directories into a flat list of file paths.

    Parameters
    ----------
    paths:
        Iterable of file or directory paths to expand.

    Returns
    -------
    List[str]
        All discovered files. Directories are searched recursively.
    """
    files: List[str] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    files.append(str(child))
        elif path.is_file():
            files.append(str(path))
    return files


def run_full_pipeline(files: List[str]) -> Dict[str, Dict]:
    """Run all available processing pipelines on the given files."""
    results: Dict[str, Dict] = {}
    results["kpis"] = compute_kpis_for_files(files)
    results["claim_metrics"] = compute_claim_metrics(files)
    results["document_metrics"] = process_documents(files)
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
