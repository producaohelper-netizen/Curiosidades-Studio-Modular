import unittest
from universal_engine.reel_caption_timing import (
    CaptionTimingError, active_caption, validate_cues,
)


class ReelCaptionTimingTests(unittest.TestCase):
    def test_selects_caption_only_during_its_audio_interval(self):
        cues = [
            {"start": 0.0, "end": 1.2, "text": "A cidade desapareceu"},
            {"start": 1.2, "end": 2.5, "text": "Mas não como você pensa"},
        ]
        validate_cues(cues, 3.0)
        self.assertEqual(active_caption(cues, 0.5), "A cidade desapareceu")
        self.assertEqual(active_caption(cues, 1.2), "Mas não como você pensa")
        self.assertEqual(active_caption(cues, 2.8), "")

    def test_rejects_overlapping_cues(self):
        with self.assertRaises(CaptionTimingError):
            validate_cues([
                {"start": 0, "end": 2, "text": "Um"},
                {"start": 1.9, "end": 3, "text": "Dois"},
            ], 4)

    def test_rejects_cues_outside_real_audio(self):
        with self.assertRaises(CaptionTimingError):
            validate_cues([{"start": 0, "end": 4, "text": "Texto"}], 2)

    def test_rejects_missing_alignment(self):
        with self.assertRaises(CaptionTimingError):
            validate_cues([], 10)


if __name__ == "__main__":
    unittest.main()
