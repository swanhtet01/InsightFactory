import os
import shutil
import tempfile
import unittest
from unittest.mock import ANY, patch

from helpers.drive_sync import sync_drive_files


class TestDriveSync(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self) -> None:
        os.chdir(self.repo_cwd)
        shutil.rmtree(self.tmpdir)

    @patch("helpers.drive_sync.download_file")
    @patch("helpers.drive_sync.list_files_in_folder")
    def test_multiple_folders(self, list_files_mock, download_mock) -> None:
        list_files_mock.side_effect = [
            [{"id": "1", "name": "a.csv", "mimeType": "application/vnd.ms-excel"}],
            [{"id": "2", "name": "b.png", "mimeType": "image/png"}],
        ]

        files = sync_drive_files(["id1", "id2"])

        self.assertEqual(set(files), {"data/a.csv", "data/images/b.png"})
        self.assertEqual(download_mock.call_count, 2)
        list_files_mock.assert_any_call("id1", ANY)
        list_files_mock.assert_any_call("id2", ANY)


if __name__ == "__main__":
    unittest.main()
