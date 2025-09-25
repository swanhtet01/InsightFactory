"""Environment and artifact readiness checks for InsightFactory."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from importlib import util
from pathlib import Path
from typing import Iterable, Sequence, TypedDict

from config import GOOGLE_DRIVE_FOLDER_IDS, REPORTS_DIR

DEFAULT_CREDENTIALS_PATH = Path("credentials.json")
DEFAULT_REQUIRED_PACKAGES = (
    "streamlit",
    "fastapi",
    "uvicorn",
    "typer",
    "pandas",
)
DEFAULT_REQUIRED_ARTIFACTS = (
    "latest_summary.json",
    "latest_dashboard.json",
    "run_history.csv",
)


class PreflightSummary(TypedDict):
    """JSON-friendly structure describing the overall preflight status."""

    status: str
    counts: dict[str, int]
    checks: list[dict[str, str | None]]


@dataclass(slots=True)
class CheckResult:
    """Outcome of a single readiness check."""

    identifier: str
    name: str
    status: str
    message: str
    remediation: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Represent the check result as a JSON-serialisable dictionary."""

        payload = asdict(self)
        payload["id"] = payload.pop("identifier")
        return payload


def _check_drive_folders(folder_ids: Sequence[str]) -> CheckResult:
    if folder_ids:
        return CheckResult(
            identifier="drive_folders",
            name="Google Drive configuration",
            status="pass",
            message=f"Configured {len(folder_ids)} folder ID(s) for ingestion.",
        )
    return CheckResult(
        identifier="drive_folders",
        name="Google Drive configuration",
        status="fail",
        message=(
            "No Drive folders configured. Set GOOGLE_DRIVE_FOLDER_IDS in the environment"
            " or provide overrides to the CLI."
        ),
        remediation=(
            "Populate GOOGLE_DRIVE_FOLDER_IDS with a comma-separated list of Drive folder"
            " identifiers before running sync or watch commands."
        ),
    )


def _check_credentials(credentials_path: Path) -> CheckResult:
    if credentials_path.exists():
        return CheckResult(
            identifier="google_credentials",
            name="Google API credentials",
            status="pass",
            message=f"Credentials file located at {credentials_path}.",
        )
    return CheckResult(
        identifier="google_credentials",
        name="Google API credentials",
        status="warn",
        message="No credentials.json found. Drive sync and watcher commands will be disabled.",
        remediation=(
            "Download a service account JSON file from Google Cloud Console and save it as"
            " credentials.json in the project root or provide the path via CLI overrides."
        ),
    )


def _check_reports_dir(path: Path) -> CheckResult:
    if path.exists() and path.is_dir():
        return CheckResult(
            identifier="reports_dir",
            name="Reports directory",
            status="pass",
            message=f"Reports directory available at {path}.",
        )
    return CheckResult(
        identifier="reports_dir",
        name="Reports directory",
        status="warn",
        message=f"Reports directory {path} not found. It will be created on demand during runs.",
        remediation="Run the analytics pipeline once to generate initial artifacts.",
    )


def _check_python_packages(packages: Iterable[str]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for package in packages:
        if util.find_spec(package) is not None:
            results.append(
                CheckResult(
                    identifier=f"pkg_{package}",
                    name=f"Python package: {package}",
                    status="pass",
                    message=f"{package} available.",
                )
            )
        else:
            results.append(
                CheckResult(
                    identifier=f"pkg_{package}",
                    name=f"Python package: {package}",
                    status="fail",
                    message=f"{package} is not installed in the current environment.",
                    remediation=f"Install {package} via pip install {package} before running the stack.",
                )
            )
    return results


def _check_artifacts(reports_dir: Path, artifacts: Iterable[str]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for artifact in artifacts:
        path = reports_dir / artifact
        if path.exists():
            results.append(
                CheckResult(
                    identifier=f"artifact_{artifact}",
                    name=f"Artifact: {artifact}",
                    status="pass",
                    message=f"Found {artifact} in {reports_dir}.",
                )
            )
        else:
            results.append(
                CheckResult(
                    identifier=f"artifact_{artifact}",
                    name=f"Artifact: {artifact}",
                    status="warn",
                    message=f"{artifact} missing from {reports_dir}.",
                    remediation=(
                        "Run the analytics pipeline to regenerate reports or confirm the REPORTS_DIR"
                        " configuration points to the correct directory."
                    ),
                )
            )
    return results


def collect_preflight_checks(
    *,
    reports_dir: Path | None = None,
    drive_folder_ids: Sequence[str] | None = None,
    credentials_path: Path | None = None,
    required_packages: Sequence[str] | None = None,
    required_artifacts: Sequence[str] | None = None,
) -> list[CheckResult]:
    """Run readiness checks and return their results."""

    resolved_reports = reports_dir or REPORTS_DIR
    resolved_drive_ids = drive_folder_ids or GOOGLE_DRIVE_FOLDER_IDS
    resolved_credentials = credentials_path or DEFAULT_CREDENTIALS_PATH
    packages = required_packages or DEFAULT_REQUIRED_PACKAGES
    artifacts = required_artifacts or DEFAULT_REQUIRED_ARTIFACTS

    results: list[CheckResult] = [
        _check_drive_folders(resolved_drive_ids),
        _check_credentials(resolved_credentials),
        _check_reports_dir(resolved_reports),
    ]

    results.extend(_check_python_packages(packages))
    results.extend(_check_artifacts(resolved_reports, artifacts))
    return results


def summarise_preflight(checks: Sequence[CheckResult]) -> PreflightSummary:
    """Summarise the overall readiness status."""

    status_order = {"fail": 0, "warn": 1, "pass": 2}
    overall_status = "pass"
    counts = {"pass": 0, "warn": 0, "fail": 0}

    for check in checks:
        counts[check.status] += 1
        if status_order[check.status] < status_order[overall_status]:
            overall_status = check.status

    return PreflightSummary(
        status=overall_status,
        counts=counts,
        checks=[check.to_dict() for check in checks],
    )


def write_summary(
    summary: PreflightSummary,
    reports_dir: Path | None = None,
    filename: str = "preflight_status.json",
) -> Path:
    """Persist the preflight summary inside the reports directory."""

    destination_dir = (reports_dir or REPORTS_DIR)
    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / filename
    import json

    target.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return target


__all__ = [
    "CheckResult",
    "collect_preflight_checks",
    "summarise_preflight",
    "write_summary",
]
