"""Real FFmpeg concat regression: clips in episodes/<id>/clips,
final video one directory higher. This layout previously always failed.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from universal_engine.production import ProductionError, concatenate, probe_duration


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg is not installed in the runner")
class ConcatenateRealVideoTests(unittest.TestCase):
    def create_clip(self,path,freq):
        video_cmd=[
            "ffmpeg","-hide_banner","-loglevel","error","-y",
            "-f","lavfi","-i","color=c=blue:s=320x180:r=24:d=0.85",
            "-f","lavfi","-i",f"sine=frequency={freq}:sample_rate=22050:duration=0.85",
            "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
            "-c:a","aac","-shortest",str(path)
        ]
        subprocess.run(video_cmd,check=True,timeout=50,capture_output=True)

    def test_output_in_parent_not_same_directory_as_clips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/"episode_01"
            folder=root/"clips";folder.mkdir(parents=True)
            clips=[folder/"clip_000.mp4",folder/"clip_001.mp4"]
            for index,file in enumerate(clips):
                self.create_clip(file,400+index*120)
            target=root/"video_provisorio.mp4"
            result=concatenate(clips,target)
            self.assertEqual(result,target)
            self.assertTrue(target.is_file())
            self.assertAlmostEqual(probe_duration(result),1.7,delta=.25)
            listing=(folder/"lista_ffmpeg.txt").read_text(encoding="utf8")
            self.assertEqual(listing.count("\n"),2)
            self.assertIn("file 'clip_000.mp4'",listing)

    def test_rejects_untrusted_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)/"clips";folder.mkdir()
            video=folder/"bad'file.mp4"
            video.write_bytes(b"x"*2048)
            with self.assertRaises(ProductionError):
                concatenate([video],folder.parent/"output.mp4")
