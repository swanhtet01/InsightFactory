import json
import importlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

import config
from helpers import drive_sync, source_registry


class TestDriveSync(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)
        self.reports_dir = Path(self.tmpdir) / "drive_reports"
        os.environ["REPORTS_DIR"] = str(self.reports_dir)

        for module in [config, source_registry, drive_sync]:
            importlib.reload(module)

    def tearDown(self) -> None:
        os.chdir(self.repo_cwd)
        shutil.rmtree(self.tmpdir)
        os.environ.pop("REPORTS_DIR", None)

    @patch("helpers.drive_sync.download_file")
    @patch("helpers.drive_sync.list_files_in_folder")
    def test_multiple_folders(self, list_files_mock, download_mock) -> None:
        list_files_mock.side_effect = [
            [{"id": "1", "name": "a.csv", "mimeType": "application/vnd.ms-excel"}],
            [{"id": "2", "name": "b.png", "mimeType": "image/png"}],
        ]

        files = drive_sync.sync_drive_files(["id1", "id2"])

        self.assertEqual(
            set(files),
            {"data/id1/spreadsheets/a.csv", "data/id2/images/b.png"},
        )
        self.assertEqual(download_mock.call_count, 2)
        list_files_mock.assert_any_call("id1", ANY)
        list_files_mock.assert_any_call("id2", ANY)

        snapshot_path = self.reports_dir / "latest_sources.json"
        self.assertTrue(snapshot_path.exists())
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(snapshot.get("total_files"), 2)
        folders = {item.get("folder_id"): item for item in snapshot.get("folders", [])}
        self.assertEqual(folders.get("id1", {}).get("files"), 1)
        self.assertEqual(folders.get("id2", {}).get("files"), 1)
        tracked_ids = {entry.get("folder_id") for entry in snapshot.get("entries", [])}
        self.assertSetEqual(tracked_ids, {"id1", "id2"})


if __name__ == "__main__":
    unittest.main()
