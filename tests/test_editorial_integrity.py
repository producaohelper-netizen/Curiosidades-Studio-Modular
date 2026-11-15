import unittest
from qa.editorial_integrity import check_storyboard


def story():
    return {"scenes": [
        {"scene_id": "a", "narration": "O polvo nada.", "visual_fact": "O polvo nada",
         "visual_query_en": "An octopus swimming through the ocean",
         "callout": "polvo", "timeline": [{"action": "move"}]},
        {"scene_id": "b", "narration": "Ele muda de cor.", "visual_fact": "Mudança de cor",
         "visual_query_en": "The octopus changing its skin color",
         "callout": "cor", "timeline": [{"action": "react"}]}
    ]}


class EditorialIntegrityTests(unittest.TestCase):
    def test_unchanged_script_passes(self):
        result = check_storyboard("O polvo nada. Ele muda de cor.", story())
        self.assertTrue(result["passed"])
        self.assertTrue(result["requires_fact_check"])

    def test_missing_narration_rejected(self):
        self.assertFalse(check_storyboard("O polvo nada. Ele muda de cor. Mais uma frase.", story())["passed"])

    def test_invented_callout_rejected(self):
        s = story()
        s["scenes"][0]["callout"] = "gigante"
        self.assertFalse(check_storyboard("O polvo nada. Ele muda de cor.", s)["passed"])

    def test_duplicate_scene_rejected(self):
        s = story()
        s["scenes"][1]["scene_id"] = "a"
        self.assertFalse(check_storyboard("O polvo nada. Ele muda de cor.", s)["passed"])

    def test_empty_story_rejected(self):
        self.assertFalse(check_storyboard("Teste", {"scenes": []})["passed"])


if __name__ == "__main__":
    unittest.main()
