import tempfile
import unittest
import wave
from pathlib import Path
from universal_engine.reel_phrase_audio import phrase_cues, join_phrase_wavs
from universal_engine.reel_caption_timing import CaptionTimingError


def write_wav(path, frames, rate=8000):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * frames)


class PhraseAudioTests(unittest.TestCase):
    def test_timestamps_match_pcm_sample_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b, out = [Path(folder) / name for name in ("a.wav", "b.wav", "full.wav")]
            write_wav(a, 4000)
            write_wav(b, 12000)
            timing = join_phrase_wavs([("Primeira frase", a), ("Segunda frase", b)], out)
            self.assertEqual(timing["duration"], 2.0)
            self.assertEqual(timing["cues"][0], {"start": 0.0, "end": 0.5, "text": "Primeira frase"})
            self.assertEqual(timing["cues"][1]["start"], 0.5)
            with wave.open(str(out), "rb") as audio:
                self.assertEqual(audio.getnframes(), 16000)

    def test_rejects_incompatible_audio_formats(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.wav", Path(folder) / "b.wav"
            write_wav(a, 8000)
            write_wav(b, 8000, rate=16000)
            with self.assertRaises(CaptionTimingError):
                phrase_cues([("Um", a), ("Dois", b)])

    def test_rejects_missing_segments(self):
        with self.assertRaises(CaptionTimingError):
            phrase_cues([])


if __name__ == "__main__":
    unittest.main()
