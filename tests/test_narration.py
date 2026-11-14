import tempfile,unittest,math,json,wave
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from universal_engine.narration import generate_piper,retime_to_audio,NarrationError
from test_scenespec import SCENES

class NarrationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.model=Path(self.temp.name)/"pt_br.onnx"
  self.model.write_bytes(b"model"*500)
  Path(str(self.model)+".json").write_text('{"language":"pt_BR"}')
  self.audio=Path(self.temp.name)/"scene.wav"
 def fake_run(self,args,**kwargs):
  path=Path(args[args.index("--output_file")+1])
  with wave.open(str(path),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
   w.writeframes(b"\x07\x00"*16000)
  return SimpleNamespace(returncode=0,stderr="")
 def test_real_wav_creation_and_cache(self):
  with patch("universal_engine.narration.subprocess.run",side_effect=self.fake_run) as mocked:
   a=generate_piper("Olá, mundo da ciência!",self.model,self.audio)
   b=generate_piper("Olá, mundo da ciência!",self.model,self.audio)
   self.assertFalse(a["reused"])
   self.assertTrue(b["reused"])
   self.assertEqual(mocked.call_count,1)
 def test_retime_preserves_narration_and_positions(self):
  src=SCENES[0]
  new=retime_to_audio(src,9)
  self.assertEqual(new["narration"],src["narration"])
  self.assertEqual(new["duration_target_seconds"],9)
  self.assertAlmostEqual(new["timeline"][2]["at"],3)
  self.assertEqual(src["duration_target_seconds"],6)
 def test_invalid_audio_time_rejected(self):
  with self.assertRaises(NarrationError):retime_to_audio(SCENES[0],120)
 def test_missing_model_rejected(self):
  with self.assertRaises(NarrationError):
   generate_piper("O polvo solta tinta",Path(self.temp.name)/"missing.onnx",self.audio)
if __name__=="__main__":unittest.main()
