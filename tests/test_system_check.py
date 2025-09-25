from __future__ import annotations

import json
from pathlib import Path

from helpers import system_check


def _touch(path: Path, contents: str = "") -> None:
    path.write_text(contents, encoding="utf-8")


def test_preflight_summary_pass(tmp_path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    _touch(reports_dir / "latest_summary.json", "{}")
    _touch(reports_dir / "latest_dashboard.json", "{}")
    _touch(reports_dir / "run_history.csv", "run_id,started_at\n")
    credentials = tmp_path / "credentials.json"
    _touch(credentials, "{}")

    checks = system_check.collect_preflight_checks(
        reports_dir=reports_dir,
        drive_folder_ids=["folder-123"],
        credentials_path=credentials,
        required_packages=["json"],
    )
    summary = system_check.summarise_preflight(checks)

    assert summary["status"] == "pass"
    assert summary["counts"] == {"pass": len(checks), "warn": 0, "fail": 0}


def test_preflight_detects_configuration_gaps(tmp_path) -> None:
    reports_dir = tmp_path / "reports"
    # Deliberately omit reports/artifacts so warnings are emitted
    missing_credentials = tmp_path / "credentials.json"

    checks = system_check.collect_preflight_checks(
        reports_dir=reports_dir,
        drive_folder_ids=[],
        credentials_path=missing_credentials,
        required_packages=["totally_fake_pkg"],
        required_artifacts=("latest_summary.json",),
    )
    status_map = {check.identifier: check.status for check in checks}

    assert status_map["drive_folders"] == "fail"
    assert status_map["google_credentials"] == "warn"
    assert status_map["pkg_totally_fake_pkg"] == "fail"
    assert status_map["reports_dir"] == "warn"

    summary = system_check.summarise_preflight(checks)
    assert summary["status"] == "fail"
    assert summary["counts"]["fail"] >= 1


def test_write_summary_creates_file(tmp_path) -> None:
    checks = [
        system_check.CheckResult("drive", "Drive", "pass", "configured"),
        system_check.CheckResult("pkg_json", "Python package: json", "pass", "available"),
    ]
    summary = system_check.summarise_preflight(checks)

    destination = system_check.write_summary(summary, reports_dir=tmp_path)
    assert destination.exists()

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert payload["counts"]["pass"] == len(checks)
