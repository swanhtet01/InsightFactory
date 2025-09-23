import os
import tempfile
from datetime import datetime
from pathlib import Path
import unittest

from helpers.data_profiler import profile_files


class TestDataProfiler(unittest.TestCase):
    def test_profile_files_with_missing_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            daily = base / "daily_report.csv"
            shift = base / "shift_notes.txt"
            daily.write_text("value\n1\n", encoding="utf-8")
            shift.write_text("notes", encoding="utf-8")

            ts_earliest = 1_700_000_000
            ts_latest = 1_700_000_500
            os.utime(daily, (ts_earliest, ts_earliest))
            os.utime(shift, (ts_latest, ts_latest))

            missing = base / "missing_weekly.xlsx"

            profile = profile_files(
                [str(daily), str(shift), str(missing), str(daily)]
            )

            self.assertEqual(profile["inputs_received"], 4)
            self.assertEqual(profile["total_files"], 3)
            self.assertEqual(profile["files_profiled"], 2)
            self.assertEqual(profile["unreadable_files"], 1)

            self.assertIn("csv", profile["extensions"])
            self.assertIn("txt", profile["extensions"])
            self.assertGreater(profile["total_bytes"], 0)
            self.assertGreater(profile["average_bytes"], 0)

            latest = datetime.fromisoformat(profile["latest_modified"])
            earliest = datetime.fromisoformat(profile["earliest_modified"])
            self.assertGreater(latest, earliest)

            tags = set(profile["granularity_tags"])
            self.assertIn("daily", tags)
            self.assertIn("shift", tags)

            self.assertTrue(
                any("daily_report.csv" in sample for sample in profile["sample_files"])
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
