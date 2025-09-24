"""Command-line interface for orchestrating InsightFactory services."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import typer

from config import REPORTS_DIR, GOOGLE_DRIVE_FOLDER_IDS
from helpers import drive_sync, drive_watcher, pipeline_runner


app = typer.Typer(help="Manage InsightFactory pipelines, syncing, and services.")


def _resolve_folders(overrides: Optional[List[str]]) -> List[str]:
    if overrides:
        return [fid for fid in overrides if fid]
    return GOOGLE_DRIVE_FOLDER_IDS


@app.command()
def sync(
    folder: List[str] = typer.Option(
        None,
        "--folder",
        "-f",
        help="Specific Google Drive folder ID(s) to sync. Defaults to configured folders.",
    )
) -> None:
    """Download spreadsheets, images, and documents from Google Drive."""

    folder_ids = _resolve_folders(folder)
    files = drive_sync.sync_drive_files(folder_ids)
    if files:
        typer.echo(f"Synced {len(files)} file(s) into local data directories.")
    else:
        if folder_ids:
            typer.echo("No files synced. Check folder IDs or recent activity.")
        else:
            typer.echo(
                "No Google Drive folders configured. Set GOOGLE_DRIVE_FOLDER_IDS or pass --folder."
            )


@app.command()
def pipeline(
    paths: List[Path] = typer.Argument(
        None,
        help="Files or directories to include. Defaults to ./data when omitted.",
    ),
) -> None:
    """Run the full analytics pipeline for the provided files/directories."""

    if not paths:
        default_data = Path("data")
        if default_data.exists():
            paths = [default_data]
        else:
            raise typer.BadParameter(
                "No paths provided and ./data does not exist. Specify files or directories."
            )

    file_args = [str(p) for p in paths]
    typer.echo(f"Collecting files from: {', '.join(file_args)}")
    files = pipeline_runner.collect_files(file_args)
    if not files:
        typer.echo("No files discovered. Nothing to process.")
        raise typer.Exit(code=0)

    typer.echo(f"Processing {len(files)} file(s) through the analytics pipeline...")
    results = pipeline_runner.run_full_pipeline(files)
    summary = results.get("run_metadata", {})
    typer.echo("Pipeline completed.")
    if summary:
        typer.echo(f"  Started at: {summary.get('started_at', 'unknown')}")
        typer.echo(f"  Duration: {summary.get('duration_seconds', 'n/a')} seconds")
        typer.echo(f"  Reports: {len(summary.get('reports_written', []))} artifact(s) updated")
    typer.echo(f"Reports directory: {REPORTS_DIR}")


@app.command()
def watch(
    interval: int = typer.Option(60, help="Polling interval (seconds) for Drive changes."),
    folder: List[str] = typer.Option(
        None,
        "--folder",
        "-f",
        help="Specific folder ID(s) to monitor. Defaults to configured folders.",
    ),
    run_once: bool = typer.Option(
        False,
        help="Perform a single sync + pipeline pass instead of an infinite watch loop.",
    ),
) -> None:
    """Continuously monitor Drive folders and process updates."""

    folder_ids = _resolve_folders(folder)
    if run_once:
        typer.echo("Running a single sync + pipeline cycle...")
        files = drive_sync.sync_drive_files(folder_ids)
        if not files:
            typer.echo("No files downloaded; skipping pipeline run.")
            return
        pipeline_runner.run_full_pipeline(files)
        typer.echo("One-off watch cycle completed.")
        return

    typer.echo(
        "Starting Drive watcher. Press Ctrl+C to stop. Polling interval: "
        f"{interval} second(s)."
    )
    drive_watcher.watch_drive_folder(interval=interval, folder_ids=folder_ids)


@app.command("serve-api")
def serve_api(
    host: str = typer.Option("0.0.0.0", help="Host interface for FastAPI."),
    port: int = typer.Option(8000, help="Port for FastAPI."),
    reload: bool = typer.Option(False, help="Enable auto-reload (development only)."),
) -> None:
    """Launch the FastAPI gateway for external consumers."""

    import uvicorn

    typer.echo(f"Starting FastAPI on http://{host}:{port}")
    uvicorn.run("api:app", host=host, port=port, reload=reload)


@app.command()
def dashboard(
    host: str = typer.Option("0.0.0.0", help="Streamlit server address."),
    port: int = typer.Option(8501, help="Streamlit server port."),
    app_path: Path = typer.Option(Path("app.py"), help="Entry Streamlit app file."),
) -> None:
    """Launch the InsightFactory Streamlit control center."""

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        host,
        "--server.port",
        str(port),
    ]
    typer.echo("Launching Streamlit dashboard...")
    typer.echo(" ".join(cmd))
    subprocess.run(cmd, check=True)


@app.command()
def status() -> None:
    """Display the most recent pipeline outputs and run history snapshot."""

    reports_dir = REPORTS_DIR
    typer.echo(f"Reports directory: {reports_dir}")
    if not reports_dir.exists():
        typer.echo("No reports directory found. Run `cli.py pipeline` to generate outputs.")
        return

    summary_path = reports_dir / "latest_summary.json"
    history_path = reports_dir / "run_history.csv"
    dashboard_path = reports_dir / "latest_dashboard.json"

    if summary_path.exists():
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        run_meta = data.get("run_metadata", {})
        typer.echo("Latest summary available.")
        if run_meta:
            typer.echo(
                f"  Last run at {run_meta.get('started_at', 'unknown')} "
                f"processing {run_meta.get('files_collected', 0)} file(s)."
            )
            typer.echo(
                f"  Health status: {run_meta.get('health_status', 'unavailable')}"
            )
    else:
        typer.echo("No latest_summary.json found.")

    if history_path.exists():
        lines = history_path.read_text(encoding="utf-8").strip().splitlines()
        typer.echo(f"Run history entries: {max(len(lines) - 1, 0)}")
    else:
        typer.echo("No run_history.csv found.")

    typer.echo(
        "Dashboard payload present." if dashboard_path.exists() else "Dashboard payload missing."
    )


def main() -> None:  # pragma: no cover - click entrypoint
    app()


if __name__ == "__main__":  # pragma: no cover
    main()

