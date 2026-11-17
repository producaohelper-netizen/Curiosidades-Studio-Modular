import tempfile
import unittest
import wave
from pathlib import Path
from universal_engine.reel_narration import synthesize_reel


def sample():
    return {
        "pillar": "historia_real", "target_seconds": 25,
        "sections": {
            "hook": "Uma cidade inteira mudou de lugar sem desaparecer.",
            "context": "Isso aconteceu quando moradores enfrentaram um problema que ameaçava a segurança de suas casas.",
            "development": "As autoridades decidiram transferir construções e serviços para outra região. A mudança exigiu planejamento, recursos e participação de muitas famílias.",
            "reveal": "A cidade não sumiu misteriosamente. Ela foi reconstruída em outro lugar, e o caso pode ser consultado em registros históricos.",
        },
        "claims": [{"text": "A cidade foi transferida", "status": "verified"}],
        "sources": [
            {"title": "A", "publisher": "Arquivo A", "url": "https://example.org/a"},
            {"title": "B", "publisher": "Arquivo B", "url": "https://example.net/b"},
        ],
    }


class ReelNarrationTests(unittest.TestCase):
    def test_generates_four_real_audio_boundaries_and_review_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            calls = []
            def synth(text, model, output, *, executable):
                calls.append(text)
                with wave.open(str(output), "wb") as audio:
                    audio.setnchannels(1)
                    audio.setsampwidth(2)
                    audio.setframerate(8000)
                    audio.writeframes(b"\x01\x00" * (8000 * 7))
                return {"path": str(output), "duration": 7}
            result = synthesize_reel(sample(), "unused.onnx", folder, synth=synth)
            self.assertEqual(len(calls), 4)
            self.assertEqual(result["audio_seconds"], 28)
            self.assertEqual(result["reel_caption_cues"][1]["start"], 7)
            self.assertFalse(result["publication_approved"])
            self.assertTrue((Path(folder) / "narracao_e_legendas.json").exists())

    def test_rejects_narration_outside_short_form_range(self):
        with tempfile.TemporaryDirectory() as folder:
            def synth(text, model, output, *, executable):
                with wave.open(str(output), "wb") as audio:
                    audio.setnchannels(1)
                    audio.setsampwidth(2)
                    audio.setframerate(8000)
                    audio.writeframes(b"\x01\x00" * 8000)
                return {}
            with self.assertRaisesRegex(ValueError, "exige 20 a 60s"):
                synthesize_reel(sample(), "unused.onnx", folder, synth=synth)


if __name__ == "__main__":
    unittest.main()
