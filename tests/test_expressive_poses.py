import unittest
from PIL import Image
from universal_engine.expressive_poses import expressive_frame, pose_index
from universal_engine.sprites import SpriteError


class ExpressivePoseTests(unittest.TestCase):
    def test_pose_progression(self):
        self.assertEqual([pose_index(t, 3, 2) for t in (0, .5, 1, 1.5)], [0, 1, 2, 0])

    def test_non_loop_holds_last_pose(self):
        self.assertEqual(pose_index(10, 3, 2, loop=False), 2)

    def test_initial_hold(self):
        self.assertEqual(pose_index(.3, 3, 2, hold_first=.5), 0)

    def test_extracts_correct_cell(self):
        sheet = Image.new("RGBA", (20, 10), (255, 0, 0, 255))
        sheet.paste((0, 255, 0, 255), (10, 0, 20, 10))
        result = expressive_frame(sheet, .5, rows=1, columns=2, frames=2, fps=2)
        self.assertEqual(result.getpixel((5, 5)), (0, 255, 0, 255))

    def test_rejects_invalid_sheet(self):
        with self.assertRaises(SpriteError):
            expressive_frame(Image.new("RGBA", (21, 10)), 0, rows=1, columns=2, frames=2)


if __name__ == "__main__":
    unittest.main()
