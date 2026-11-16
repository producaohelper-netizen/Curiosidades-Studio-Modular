"""Real FFmpeg smoke test: render a short portrait MP4 with timed captions.

Uses generated test WAV/images, not third-party media. Does not validate Piper,
story truth, visual relevance or publication quality.
"""
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from PIL import Image
from universal_engine.reel_render import render_reel


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg/FFprobe unavailable")
class ReelRenderIntegrationTests(unittest.TestCase):
    def test_actual_portrait_mp4_with_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            audio = root / "voice.wav"
            with wave.open(str(audio), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(8000)
                wav.writeframes(b"\x01\x00" * 16000)
            cues = []
            images = []
            for i in range(4):
                path = root / f"visual_{i}.png"
                Image.new("RGB", (90, 160), (20 + i * 40, 40, 90)).save(path)
                images.append(path)
                cues.append({"start": i * .5, "end": (i + 1) * .5,
                             "text": f"Trecho {i+1}"})
            output = root / "review.mp4"
            report = render_reel(audio, cues, images, output,
                                 size=(180, 320), fps=12)
            self.assertTrue(output.is_file())
            self.assertFalse(report["publication_approved"])
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "stream=codec_type,width,height", "-of", "json", str(output)],
                capture_output=True, text=True, check=True)
            import json
            streams = json.loads(probe.stdout)["streams"]
            video = next(s for s in streams if s["codec_type"] == "video")
            self.assertEqual((video["width"], video["height"]), (180, 320))
            self.assertTrue(any(s["codec_type"] == "audio" for s in streams))


if __name__ == "__main__":
    unittest.main()
