"""Trending-topic rotation tests: no invented topic and no repeat of recent episodes."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from universal_engine.production import Settings, choose_topic, ProductionError


class TopicRotationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings = Settings(self.tmp.name, "unused.onnx")
        self.trends = [
            {"title": "Polvos", "source": "RSS", "traffic_label": "high"},
            {"title": "Vulcões", "source": "RSS", "traffic_label": "medium"},
        ]

    def record(self, folder, title):
        path = Path(self.tmp.name) / "episodes" / folder / "status.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"topic": {"title": title}}), encoding="utf8")

    def select(self):
        with patch("universal_engine.production.fetch_trends", return_value=self.trends), \
             patch("universal_engine.production.top_five", side_effect=lambda items: items):
            return choose_topic(self.settings)

    def test_first_topic_when_history_empty(self):
        self.assertEqual(self.select()["title"], "Polvos")

    def test_skips_recently_used_topic(self):
        self.record("20261115_a", "POLVOS")
        self.assertEqual(self.select()["title"], "Vulcões")

    def test_does_not_repeat_when_all_trends_exhausted(self):
        self.record("20261115_a", "Polvos")
        self.record("20261115_b", "Vulcões")
        with self.assertRaisesRegex(ProductionError, "já foram utilizadas"):
            self.select()

    def test_manual_topic_remains_available(self):
        self.settings.topic = "Como funcionam os foguetes"
        self.assertEqual(choose_topic(self.settings)["title"], self.settings.topic)


if __name__ == "__main__":
    unittest.main()
