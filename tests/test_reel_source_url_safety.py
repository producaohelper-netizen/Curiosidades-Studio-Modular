"""Regression tests for editorial source URL sanitation."""
import unittest
from universal_engine.shortform import ShortFormError, validate_reel


class EditorialSourceUrlTests(unittest.TestCase):
    def payload(self, bad_url):
        return {
            "pillar": "historia_real", "target_seconds": 25,
            "sections": {"hook": "Um fato surpreendente", "context": " ".join(["Contexto"] * 12),
                         "development": " ".join(["Detalhe"] * 16), "reveal": " ".join(["Conclusão"] * 12)},
            "claims": [{"text": "Um fato para revisar", "status": "unknown"}],
            "sources": [
                {"title": "Primeira", "publisher": "Editora A", "url": bad_url},
                {"title": "Segunda", "publisher": "Editora B", "url": "https://example.org/report"},
            ],
        }

    def test_rejects_invalid_whitespace_and_control_characters(self):
        for url in (
            "https://example.com/with space",
            "https://example.com/with\\tTab",
            "https://example.com/with\\nnewline",
            "https://example.com/with\\rreturn",
            "https://example.com/with\\x7fdel",
        ):
            with self.subTest(url=repr(url)):
                with self.assertRaises(ShortFormError):
                    validate_reel(self.payload(url))

    def test_valid_independent_sources_remain_accepted(self):
        result = validate_reel(self.payload("https://example.com/report"))
        self.assertFalse(result["publication_approved"])


if __name__ == "__main__":
    unittest.main()
