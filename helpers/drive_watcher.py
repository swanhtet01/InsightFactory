"""Resilient Google Drive watcher for continuous pipeline automation."""

from __future__ import annotations

import logging
from typing import Iterable, Optional, Sequence

from helpers.drive_sync import sync_drive_files
from helpers.drive_browser import get_drive_service
from helpers.pipeline_runner import run_full_pipeline
from config import GOOGLE_DRIVE_FOLDER_IDS


LOGGER = logging.getLogger(__name__)


def _sleep(seconds: float) -> None:
    """Wrapper around time.sleep for easier testing overrides."""

    import time

    time.sleep(seconds)


def watch_drive_folder(
    interval: int = 60,
    folder_ids: Optional[Iterable[str]] = None,
    *,
    sync_on_start: bool = True,
    max_cycles: Optional[int] = None,
    backoff_factor: float = 2.0,
    max_backoff: float = 300.0,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Watch configured Drive folders and trigger the analytics pipeline on change.

    Parameters
    ----------
    interval:
        Base polling interval in seconds for Drive change detection.
    folder_ids:
        Optional iterable of Drive folder IDs to monitor. Defaults to
        :data:`config.GOOGLE_DRIVE_FOLDER_IDS` when omitted.
    sync_on_start:
        When ``True`` (default) the watcher performs an initial sync and pipeline
        execution before entering the change polling loop.
    max_cycles:
        Optional number of polling iterations to run. Useful for unit tests or
        deterministic batch execution. ``None`` (default) keeps the watcher
        running indefinitely.
    backoff_factor:
        Multiplier used for exponential backoff after consecutive errors.
    max_backoff:
        Maximum number of seconds to sleep after an error is encountered.
    logger:
        Optional :class:`logging.Logger` for status output. Defaults to the
        module logger when not provided.
    """

    resolved_logger = logger or LOGGER
    folders: Sequence[str] = tuple(folder_ids or GOOGLE_DRIVE_FOLDER_IDS)
    if not folders:
        resolved_logger.warning(
            "Drive watcher exiting: no folder IDs configured. Set GOOGLE_DRIVE_FOLDER_IDS."
        )
        return

    service = get_drive_service()
    start_response = service.changes().getStartPageToken().execute()
    page_token = start_response.get("startPageToken")
    if not page_token:
        resolved_logger.warning("Drive watcher could not obtain a start page token; exiting.")
        return

    folder_ids_set = set(folders)
    cycles = 0
    consecutive_errors = 0

    def _should_stop() -> bool:
        return max_cycles is not None and cycles >= max_cycles

    if sync_on_start:
        try:
            resolved_logger.info("Performing initial Drive sync before starting watcher loop.")
            files = sync_drive_files(folders)
            if files:
                run_full_pipeline(files)
        except Exception as exc:  # pragma: no cover - defensive logging
            consecutive_errors += 1
            resolved_logger.exception("Initial Drive sync failed: %s", exc)

    while not _should_stop():
        try:
            response = service.changes().list(
                pageToken=page_token,
                spaces="drive",
                fields=(
                    "nextPageToken, newStartPageToken, "
                    "changes(fileId, removed, file(id, name, mimeType, parents))"
                ),
            ).execute()
            consecutive_errors = 0
        except Exception as exc:  # pragma: no cover - network/auth exceptions
            consecutive_errors += 1
            sleep_seconds = min(interval * (backoff_factor ** (consecutive_errors - 1)), max_backoff)
            resolved_logger.exception(
                "Drive change polling failed (attempt %s). Retrying in %.1f seconds.",
                consecutive_errors,
                sleep_seconds,
                exc_info=exc,
            )
            _sleep(sleep_seconds)
            cycles += 1
            continue

        for change in response.get("changes", []):
            file = change.get("file")
            if not file or change.get("removed"):
                continue
            parents = set(file.get("parents") or [])
            if not (parents & folder_ids_set):
                continue
            resolved_logger.info("Detected Drive change in %s", file.get("name") or file.get("id"))
            try:
                files = sync_drive_files(folders)
                if files:
                    run_full_pipeline(files)
            except Exception as exc:  # pragma: no cover - pipeline issues
                consecutive_errors += 1
                sleep_seconds = min(interval * (backoff_factor ** (consecutive_errors - 1)), max_backoff)
                resolved_logger.exception(
                    "Processing Drive change failed (attempt %s). Waiting %.1f seconds before retry.",
                    consecutive_errors,
                    sleep_seconds,
                    exc_info=exc,
                )
                _sleep(sleep_seconds)
                break

        if "newStartPageToken" in response:
            page_token = response["newStartPageToken"]
        elif response.get("nextPageToken"):
            page_token = response["nextPageToken"]

        cycles += 1
        if _should_stop():
            break
        _sleep(interval)


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    files = sync_drive_files()
    if files:
        run_full_pipeline(files)
    watch_drive_folder()

