import unittest
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from universal_engine.reel_render import render_reel, ReelRenderError, main, visual_section_at


class ReelRenderTests(unittest.TestCase):
    def test_visual_selection_retains_previous_section_during_silence(self):
        cues = [
            {"start": 0.5, "end": 1.5, "text": "A"},
            {"start": 2.0, "end": 3.0, "text": "B"},
            {"start": 3.5, "end": 4.0, "text": "C"},
        ]
        self.assertEqual(visual_section_at(cues, 0.0), 0)
        self.assertEqual(visual_section_at(cues, 0.7), 0)
        self.assertEqual(visual_section_at(cues, 1.5), 0)
        self.assertEqual(visual_section_at(cues, 1.99), 0)
        self.assertEqual(visual_section_at(cues, 2.0), 1)
        self.assertEqual(visual_section_at(cues, 3.25), 1)
        self.assertEqual(visual_section_at(cues, 3.5), 2)
        self.assertEqual(visual_section_at(cues, 4.5), 2)

    def test_visual_selection_rejects_empty_cues(self):
        with self.assertRaises(ValueError):
            visual_section_at([], 0.0)

    def test_requires_exact_visual_for_each_narrated_section(self):
        with self.assertRaisesRegex(ReelRenderError, "imagem por trecho"):
            render_reel("missing.wav", [{"start": 0, "end": 1, "text": "A"}],
                        [], "unused.mp4")

    def test_rejects_horizontal_export(self):
        with self.assertRaisesRegex(ReelRenderError, "vertical"):
            render_reel("missing.wav", [{"start": 0, "end": 1, "text": "A"}],
                        ["missing.png"], "unused.mp4", size=(1920, 1080))


    def test_invalid_license_manifest_blocks_render_before_mp4(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "narration.json"
            script.write_text(json.dumps({"audio_path": "not-needed.wav",
                                          "reel_caption_cues": []}), encoding="utf8")
            rights = root / "rights.json"
            rights.write_text(json.dumps({"assets": []}), encoding="utf8")
            output = root / "reel.mp4"
            argv = ["reel_render", "--narration-json", str(script), "--images",
                    "a.png", "b.png", "c.png", "d.png",
                    "--license-manifest", str(rights), "--output", str(output)]
            with patch.object(sys, "argv", argv), patch(
                    "universal_engine.reel_render.render_reel") as renderer:
                with self.assertRaises(SystemExit) as error:
                    main()
                self.assertEqual(error.exception.code, 2)
                renderer.assert_not_called()
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
