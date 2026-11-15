import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from universal_engine.bootstrap import (
    BootstrapError, check_runtime, download_model, setup, missing_packages, find_ffmpeg_bin,
)

class BootstrapTests(unittest.TestCase):
    def test_bootstrap_does_not_download_voice_twice(self):
        with tempfile.TemporaryDirectory() as temp:
            model=Path(temp)/"pt_BR-faber-medium.onnx"
            with model.open("wb") as stream:
                stream.seek(30_000_002);stream.write(b"x")
            Path(str(model)+".json").write_text('{"audio":{"sample_rate":22050}}'+" "*400)
            def fail_request(*args,**kwargs):
                raise AssertionError("Cached files should not be downloaded")
            self.assertEqual(download_model(model,opener=fail_request),model)
    def test_discovers_previous_ffmpeg_tools_directory(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)/"tools"/"ffmpeg"/"bin"
            folder.mkdir(parents=True)
            import os
            for name in (("ffmpeg.exe","ffprobe.exe") if os.name=="nt" else ("ffmpeg","ffprobe")):
                (folder/name).write_bytes(b"fixture")
            with patch("universal_engine.bootstrap.shutil.which",return_value=None):
                self.assertTrue(Path(find_ffmpeg_bin(Path(d)/"models"/"voice.onnx")).samefile(folder))
    def test_invalid_voice_download_is_atomic(self):
        with tempfile.TemporaryDirectory() as temp:
            model=Path(temp)/"pt_BR-faber-medium.onnx"
            def too_short(request,timeout):
                return io.BytesIO(b"incomplete")
            with self.assertRaises(BootstrapError):
                download_model(model,opener=too_short)
            self.assertFalse(model.exists())
            self.assertFalse(model.with_suffix(".onnx.partial").exists())
    def test_missing_dependency_halts_without_running_install_when_disabled(self):
        with self.assertRaises(BootstrapError):
            check_runtime(voice_path="/tmp/missing-voice",
                          packages=["open_clip_torch"],install=False)
    def test_runtime_report_never_claims_artistic_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            model=Path(temp)/"pt_BR-faber-medium.onnx"
            with patch("universal_engine.bootstrap.shutil.which",
                       return_value="/usr/bin/tool"),patch(
                       "universal_engine.bootstrap.piper_executable",
                       return_value="/usr/bin/piper"):
                result=check_runtime(voice_path=model,packages=[],
                      downloader=lambda p: (p.write_bytes(b"stub"),
                        Path(str(p)+".json").write_text("{}")))
            self.assertEqual(result["publisher_approval"],"not_automated")
            self.assertEqual(result["status"],"ready_dependencies")
