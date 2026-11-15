import tempfile
import unittest
import wave
from pathlib import Path
from universal_engine.mouth_sync import wav_envelope, mouth_pose_at, MouthSyncError


def write_wav(path, data):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(1000)
        wav.writeframes(data)


class MouthSyncTests(unittest.TestCase):
    def test_silent_audio_closed_mouth(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "silence.wav"
            write_wav(path, b"\x00\x00" * 100)
            envelope = wav_envelope(path, window_ms=50)
            self.assertEqual(mouth_pose_at(envelope, 0), 0)

    def test_loud_audio_wide_mouth(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "loud.wav"
            write_wav(path, b"\xff\x7f" * 100)
            envelope = wav_envelope(path, window_ms=50)
            self.assertEqual(mouth_pose_at(envelope, .05), 2)

    def test_thresholds(self):
        envelope = {"window_ms": 50, "amplitudes": [0, .05, .2]}
        self.assertEqual([mouth_pose_at(envelope, t) for t in (0, .05, .1)], [0, 1, 2])

    def test_invalid_time(self):
        with self.assertRaises(MouthSyncError):
            mouth_pose_at({"window_ms": 50, "amplitudes": [.2]}, float("nan"))


if __name__ == "__main__":
    unittest.main()
