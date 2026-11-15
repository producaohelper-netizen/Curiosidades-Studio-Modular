import tempfile
import unittest
from pathlib import Path
from qa.visual_repetition_audit import audit_scene_backgrounds


class VisualRepetitionTests(unittest.TestCase):
    def test_identical_backgrounds_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            a = Path(folder) / "a.png"
            b = Path(folder) / "b.png"
            c = Path(folder) / "c.png"
            a.write_bytes(b"same visual data")
            b.write_bytes(b"same visual data")
            c.write_bytes(b"other visual data")
            report = audit_scene_backgrounds([
                ("scene_001", a), ("scene_002", b), ("scene_003", c)
            ])
            self.assertEqual(report["unique_backgrounds"], 2)
            self.assertEqual(report["repeated_background_groups"], [["scene_001", "scene_002"]])
            self.assertTrue(report["visual_review_required"])

    def test_distinct_backgrounds_not_flagged(self):
        with tempfile.TemporaryDirectory() as folder:
            files = [Path(folder) / f"{i}.png" for i in range(3)]
            for i, path in enumerate(files):
                path.write_bytes(str(i).encode())
            report = audit_scene_backgrounds([(str(i), path) for i, path in enumerate(files)])
            self.assertFalse(report["visual_review_required"])
            self.assertEqual(report["repeated_scene_count"], 0)


if __name__ == "__main__":
    unittest.main()
