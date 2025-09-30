"""Tests for the resilient Google Drive watcher."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call, patch


class DriveWatcherTests(unittest.TestCase):
    @patch("helpers.drive_watcher.run_full_pipeline")
    @patch("helpers.drive_watcher.sync_drive_files")
    @patch("helpers.drive_watcher.get_drive_service")
    @patch("helpers.drive_watcher._sleep")
    def test_initial_sync_and_change_processing(
        self, sleep_mock, service_mock, sync_mock, pipeline_mock
    ) -> None:
        """Watcher performs an initial sync and processes detected changes."""

        changes_mock = MagicMock()
        changes_mock.getStartPageToken.return_value.execute.return_value = {
            "startPageToken": "token-1"
        }
        changes_mock.list.return_value.execute.return_value = {
            "changes": [
                {
                    "file": {"id": "file-1", "name": "report.xlsx", "parents": ["folder"]},
                    "removed": False,
                }
            ],
            "newStartPageToken": "token-2",
        }
        service_mock.return_value.changes.return_value = changes_mock

        sync_mock.side_effect = [["initial.csv"], ["changed.csv"]]

        from helpers.drive_watcher import watch_drive_folder

        watch_drive_folder(interval=5, folder_ids=["folder"], max_cycles=1)

        self.assertEqual(sync_mock.call_count, 2)
        self.assertEqual(pipeline_mock.call_count, 2)
        sleep_mock.assert_not_called()

    @patch("helpers.drive_watcher.run_full_pipeline")
    @patch("helpers.drive_watcher.sync_drive_files")
    @patch("helpers.drive_watcher.get_drive_service")
    @patch("helpers.drive_watcher._sleep")
    def test_error_backoff_keeps_watcher_running(
        self, sleep_mock, service_mock, sync_mock, pipeline_mock
    ) -> None:
        """Transient errors trigger backoff sleeps without crashing the watcher."""

        changes_mock = MagicMock()
        changes_mock.getStartPageToken.return_value.execute.return_value = {
            "startPageToken": "token-1"
        }
        # First poll raises, second poll returns no changes so the loop can exit.
        changes_mock.list.return_value.execute.side_effect = [
            RuntimeError("boom"),
            {"changes": []},
        ]
        service_mock.return_value.changes.return_value = changes_mock

        sync_mock.return_value = []

        from helpers.drive_watcher import watch_drive_folder

        watch_drive_folder(
            interval=10,
            folder_ids=["folder"],
            max_cycles=2,
            sync_on_start=False,
            backoff_factor=2.0,
        )

        # Only the backoff sleep fires because the loop exits before the interval pause.
        sleep_mock.assert_has_calls([call(10.0)])
        pipeline_mock.assert_not_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
