"""Production preflight must preserve narration and visual direction.

These tests exercise the actual editorial gate invoked before expensive TTS.
"""
import unittest
from qa.editorial_integrity import check_storyboard


def storyboard(text, *, visual="A curious octopus explores a coral reef underwater"):
    return {"scenes": [{
        "scene_id": "scene_000", "narration": text,
        "visual_fact": "O polvo explora um recife",
        "visual_query_en": visual, "timeline": [{"action": "react", "target": "octopus", "at": 0}],
        "callout": ""
    }]}


class ProductionEditorialGateTests(unittest.TestCase):
    def test_complete_storyboard_passes(self):
        self.assertTrue(check_storyboard("O polvo explora o recife.", storyboard("O polvo explora o recife."))["passed"])

    def test_missing_narration_rejected(self):
        self.assertFalse(check_storyboard("O polvo explora o recife.", storyboard("O polvo explora."))["passed"])

    def test_repeated_or_rewritten_narration_rejected(self):
        self.assertFalse(check_storyboard("O polvo explora o recife.", storyboard("O polvo explora o recife. O polvo explora o recife."))["passed"])

    def test_generic_visual_description_rejected(self):
        self.assertFalse(check_storyboard("O polvo explora o recife.", storyboard("O polvo explora o recife.", visual="animal"))["passed"])


if __name__ == "__main__":
    unittest.main()
