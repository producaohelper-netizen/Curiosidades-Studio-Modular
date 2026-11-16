import unittest
from universal_engine.shortform import PILLARS, ShortFormError, choose_pillar, validate_reel


def example():
    return {
        "pillar": "historia_real", "target_seconds": 25,
        "sections": {
            "hook": "Uma cidade inteira mudou de lugar sem desaparecer.",
            "context": "Isso aconteceu quando moradores enfrentaram um problema que ameaçava a segurança de suas casas.",
            "development": "As autoridades decidiram transferir construções e serviços para outra região. A mudança exigiu planejamento, recursos e participação de muitas famílias.",
            "reveal": "A cidade não sumiu misteriosamente. Ela foi reconstruída em outro lugar, e o caso pode ser consultado em registros históricos.",
        },
        "claims": [{"text": "A cidade foi transferida.", "status": "verified"}],
        "sources": [
            {"title": "Registro A", "url": "https://example.org/a", "publisher": "Arquivo A"},
            {"title": "Registro B", "url": "https://example.org/b", "publisher": "Arquivo B"},
        ],
    }


class ShortFormTests(unittest.TestCase):
    def test_editorial_mix_starts_with_history(self):
        self.assertEqual(choose_pillar({}), "historia_real")

    def test_rotation_compensates_overrepresented_history(self):
        self.assertNotEqual(choose_pillar({"historia_real": 10}), "historia_real")

    def test_reel_contract_uses_vertical_video_and_requires_review(self):
        result = validate_reel(example())
        self.assertEqual((result["format"]["width"], result["format"]["height"]), (1080, 1920))
        self.assertFalse(result["publication_approved"])
        self.assertTrue(result["narration"].startswith("Uma cidade"))

    def test_missing_independent_source_rejected(self):
        data = example()
        data["sources"] = data["sources"][:1]
        with self.assertRaises(ShortFormError):
            validate_reel(data)

    def test_same_site_is_not_independent_evidence(self):
        data = example()
        data["sources"][1]["url"] = "https://www.example.org/other"
        with self.assertRaisesRegex(ShortFormError, "sites diferentes"):
            validate_reel(data)

    def test_same_publisher_is_not_independent_evidence(self):
        data = example()
        data["sources"][1]["publisher"] = "arquivo a"
        with self.assertRaisesRegex(ShortFormError, "responsáveis"):
            validate_reel(data)

    def test_invalid_source_hostname_rejected(self):
        data = example()
        data["sources"][1]["url"] = "https://"
        with self.assertRaises(ShortFormError):
            validate_reel(data)

    def test_missing_reveal_rejected(self):
        data = example()
        data["sections"]["reveal"] = ""
        with self.assertRaises(ShortFormError):
            validate_reel(data)

    def test_unclassified_claim_rejected(self):
        data = example()
        data["claims"][0]["status"] = "true"
        with self.assertRaises(ShortFormError):
            validate_reel(data)


if __name__ == "__main__":
    unittest.main()
