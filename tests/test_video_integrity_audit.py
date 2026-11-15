import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from qa.video_integrity_audit import parse_ranges, audit


class VideoIntegrityAuditTests(unittest.TestCase):
    def test_detect_intervals(self):
        log = "black_start:1.0 black_end:3.5\nblack_start:8 black_end:9"
        self.assertEqual(parse_ranges(log, "black_start", "black_end"),
                         [{"start": 1.0, "end": 3.5, "seconds": 2.5},
                          {"start": 8.0, "end": 9.0, "seconds": 1.0}])

    def test_missing_video(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                audit(Path(d) / "missing.mp4")

    def test_invalid_intervals_ignored(self):
        self.assertEqual(parse_ranges("black_start:5 black_end:3", "black_start", "black_end"), [])


if __name__ == "__main__":
    unittest.main()
