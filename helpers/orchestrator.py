"""Utilities for launching the InsightFactory stack as a single service."""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from contextlib import suppress
from multiprocessing import Process
from pathlib import Path
from typing import Callable, Optional, Sequence

from helpers.drive_watcher import watch_drive_folder


LOGGER = logging.getLogger(__name__)


def build_api_command(host: str, port: int, reload: bool = False) -> list[str]:
    """Return the command list used to launch the FastAPI gateway."""

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "api:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        command.append("--reload")
    return command


def build_dashboard_command(host: str, port: int, app_path: Path) -> list[str]:
    """Return the command list used to launch the Streamlit dashboard."""

    return [
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


def _launch_drive_watcher(
    *,
    interval: int,
    folder_ids: Optional[Sequence[str]],
    sync_on_start: bool,
) -> Process:
    """Start the Drive watcher in a background process."""

    process = Process(
        target=watch_drive_folder,
        kwargs={
            "interval": interval,
            "folder_ids": tuple(folder_ids) if folder_ids else None,
            "sync_on_start": sync_on_start,
        },
        daemon=True,
    )
    process.start()
    return process


def _terminate_subprocess(proc: subprocess.Popen[bytes], name: str, logger: logging.Logger) -> None:
    """Terminate a ``subprocess.Popen`` instance if it is still running."""

    if proc.poll() is None:
        logger.info("Stopping %s...", name)
        proc.terminate()
        with suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=10)


def _terminate_process(proc: Process, name: str, logger: logging.Logger) -> None:
    """Terminate a :class:`multiprocessing.Process` if it is still alive."""

    if proc.is_alive():
        logger.info("Stopping %s...", name)
        proc.terminate()
    proc.join(timeout=10)


def run_stack(
    *,
    interval: int = 60,
    folder_ids: Optional[Sequence[str]] = None,
    sync_on_start: bool = True,
    api_host: str = "0.0.0.0",
    api_port: int = 8000,
    api_reload: bool = False,
    dashboard_host: str = "0.0.0.0",
    dashboard_port: int = 8501,
    app_path: Path = Path("app.py"),
    run_duration: Optional[float] = None,
    poll_interval: float = 1.0,
    logger: Optional[logging.Logger] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> None:
    """Launch the Drive watcher, FastAPI gateway, and dashboard together.

    Parameters
    ----------
    interval:
        Polling interval (seconds) for Drive change detection.
    folder_ids:
        Optional set of Drive folder IDs to watch. Defaults to the values defined
        in the environment configuration when ``None``.
    sync_on_start:
        When ``True`` (default) the Drive watcher performs an initial sync before
        monitoring for changes.
    api_host / api_port:
        Binding configuration for the FastAPI gateway.
    api_reload:
        When ``True`` the FastAPI server runs with auto-reload (development only).
    dashboard_host / dashboard_port:
        Binding configuration for the Streamlit dashboard.
    app_path:
        Streamlit entry point.
    run_duration:
        Optional number of seconds to run before shutting the stack down. ``None``
        keeps the processes alive until a KeyboardInterrupt is raised. Intended
        primarily for automated tests.
    poll_interval:
        Delay between liveness checks.
    logger:
        Optional logger for status output. Defaults to this module's logger.
    sleep_fn:
        Override for time.sleep used in tests.
    """

    resolved_logger = logger or LOGGER
    sleeper: Callable[[float], None]
    if sleep_fn is not None:
        sleeper = sleep_fn
    else:
        sleeper = time.sleep

    resolved_logger.info("Launching InsightFactory stack: watcher, API, dashboard")

    watcher_process = _launch_drive_watcher(
        interval=interval,
        folder_ids=folder_ids,
        sync_on_start=sync_on_start,
    )
    api_process = subprocess.Popen(
        build_api_command(api_host, api_port, reload=api_reload),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    dashboard_process = subprocess.Popen(
        build_dashboard_command(dashboard_host, dashboard_port, app_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    start = time.monotonic()

    try:
        while True:
            if api_process.poll() is not None:
                raise RuntimeError("FastAPI process exited unexpectedly")
            if dashboard_process.poll() is not None:
                raise RuntimeError("Streamlit process exited unexpectedly")
            if watcher_process.exitcode not in (None, 0):
                raise RuntimeError(
                    f"Drive watcher exited unexpectedly with code {watcher_process.exitcode}"
                )

            if run_duration is not None and (time.monotonic() - start) >= run_duration:
                break

            sleeper(poll_interval)
    except KeyboardInterrupt:  # pragma: no cover - manual interruption path
        resolved_logger.info("Keyboard interrupt received. Shutting down stack.")
    finally:
        _terminate_subprocess(api_process, "FastAPI server", resolved_logger)
        _terminate_subprocess(dashboard_process, "Streamlit dashboard", resolved_logger)
        _terminate_process(watcher_process, "Drive watcher", resolved_logger)

