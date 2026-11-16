import unittest
from universal_engine.reel_render import render_reel, ReelRenderError


class ReelRenderTests(unittest.TestCase):
    def test_requires_exact_visual_for_each_narrated_section(self):
        with self.assertRaisesRegex(ReelRenderError, "imagem por trecho"):
            render_reel("missing.wav", [{"start": 0, "end": 1, "text": "A"}],
                        [], "unused.mp4")

    def test_rejects_horizontal_export(self):
        with self.assertRaisesRegex(ReelRenderError, "vertical"):
            render_reel("missing.wav", [{"start": 0, "end": 1, "text": "A"}],
                        ["missing.png"], "unused.mp4", size=(1920, 1080))


if __name__ == "__main__":
    unittest.main()
