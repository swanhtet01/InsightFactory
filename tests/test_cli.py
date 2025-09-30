from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import warnings

import click
import pytest

# Silence Click/Typer deprecation noise during CLI tests.
warnings.filterwarnings("ignore", message=".*BaseCommand.*", category=DeprecationWarning)
warnings.filterwarnings(
    "ignore", message=".*__version__ attribute.*", category=DeprecationWarning
)

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    version = getattr(click, "__version__", "8.1.7")
click.__version__ = version if isinstance(version, str) else "8.1.7"

import cli


runner = CliRunner()


def test_pipeline_command_invokes_runner(tmp_path, monkeypatch):
    collected_paths = {}

    def fake_collect(paths):
        collected_paths["paths"] = list(paths)
        return [str(tmp_path / "file.csv")]

    def fake_run(files):
        collected_paths["files"] = list(files)
        return {
            "run_metadata": {
                "started_at": "2024-01-01T00:00:00Z",
                "duration_seconds": 1.23,
                "reports_written": ["reports/latest_summary.json"],
            }
        }

    monkeypatch.setattr(cli.pipeline_runner, "collect_files", fake_collect)
    monkeypatch.setattr(cli.pipeline_runner, "run_full_pipeline", fake_run)

    result = runner.invoke(cli.app, ["pipeline", str(tmp_path)])
    assert result.exit_code == 0
    assert collected_paths["paths"] == [str(tmp_path)]
    assert collected_paths["files"] == [str(tmp_path / "file.csv")]
    assert "Pipeline completed." in result.stdout


def test_sync_command_reports_download(monkeypatch):
    monkeypatch.setattr(cli.drive_sync, "sync_drive_files", lambda folder_ids=None: ["a", "b"])

    result = runner.invoke(cli.app, ["sync", "--folder", "abc"])

    assert result.exit_code == 0
    assert "Synced 2 file(s)" in result.stdout


def test_watch_run_once_executes_pipeline(monkeypatch):
    state = {}

    def fake_sync(folder_ids=None):
        state["synced"] = folder_ids
        return ["/tmp/sample.xlsx"]

    def fake_run(files):
        state["processed"] = list(files)
        return {}

    monkeypatch.setattr(cli.drive_sync, "sync_drive_files", fake_sync)
    monkeypatch.setattr(cli.pipeline_runner, "run_full_pipeline", fake_run)

    result = runner.invoke(cli.app, ["watch", "--run-once", "--folder", "folder-123", "--interval", "5"])

    assert result.exit_code == 0
    assert state["synced"] == ["folder-123"]
    assert state["processed"] == ["/tmp/sample.xlsx"]
    assert "One-off watch cycle completed." in result.stdout


def test_status_command_reports_artifacts(tmp_path, monkeypatch):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    summary_path = reports_dir / "latest_summary.json"
    history_path = reports_dir / "run_history.csv"
    dashboard_path = reports_dir / "latest_dashboard.json"

    summary_path.write_text(
        json.dumps({"run_metadata": {"started_at": "2024-01-01", "files_collected": 5}}),
        encoding="utf-8",
    )
    history_path.write_text("timestamp\n2024-01-01\n", encoding="utf-8")
    dashboard_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(cli, "REPORTS_DIR", reports_dir)

    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0
    assert "Latest summary available." in result.stdout
    assert "Run history entries: 1" in result.stdout
    assert "Dashboard payload present." in result.stdout


def test_preflight_command_outputs_summary(monkeypatch):
    received: dict[str, object] = {}
    checks = [
        cli.system_check.CheckResult("drive", "Drive", "pass", "configured"),
        cli.system_check.CheckResult("reports", "Reports", "warn", "missing", "run pipeline"),
    ]

    def fake_collect(**kwargs):
        received.update(kwargs)
        return checks

    def fake_summary(results):
        assert results == checks
        return {
            "status": "warn",
            "counts": {"pass": 1, "warn": 1, "fail": 0},
            "checks": [check.to_dict() for check in checks],
        }

    saved_paths: list[Path] = []

    def fake_write(summary, reports_dir=None):
        saved = Path("/tmp/preflight.json")
        saved_paths.append(saved)
        return saved

    monkeypatch.setattr(cli.system_check, "collect_preflight_checks", fake_collect)
    monkeypatch.setattr(cli.system_check, "summarise_preflight", fake_summary)
    monkeypatch.setattr(cli.system_check, "write_summary", fake_write)

    result = runner.invoke(
        cli.app,
        ["preflight", "--folder", "demo", "--json", "--write"],
    )

    assert result.exit_code == 0
    assert received["drive_folder_ids"] == ["demo"]
    assert "\"status\": \"warn\"" in result.stdout
    assert saved_paths, "preflight summary should be saved when --write is provided"


def test_stack_command_invokes_orchestrator(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_stack(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(cli.orchestrator, "run_stack", fake_run_stack)

    result = runner.invoke(
        cli.app,
        [
            "stack",
            "--interval",
            "15",
            "--folder",
            "plant-123",
            "--duration",
            "0",
            "--dashboard-port",
            "8700",
            "--api-port",
            "9100",
            "--no-sync-on-start",
        ],
    )

    assert result.exit_code == 0
    assert captured["interval"] == 15
    assert captured["folder_ids"] == ["plant-123"]
    assert captured["sync_on_start"] is False
    assert captured["api_port"] == 9100
    assert captured["dashboard_port"] == 8700
    assert captured["run_duration"] == 0.0
