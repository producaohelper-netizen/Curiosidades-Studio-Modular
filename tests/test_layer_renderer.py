import shutil
import tempfile
import unittest
import wave
from pathlib import Path
from PIL import Image, ImageChops
from universal_engine.layer_renderer import render_frame, render_clip, RenderError
from test_scenespec import SCENES

class LayerRendererTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
  self.background=self.root/"bg.png"
  Image.new("RGB",(600,340),"#16416b").save(self.background)
  self.assets={}
  for actor in SCENES[0]["actors"]:
   path=self.root/(actor["asset_id"]+".png")
   Image.new("RGBA",(100,100),(255,130,65,220)).save(path)
   self.assets[actor["asset_id"]]=path
 def _wav(self,length=1.0):
  path=self.root/"voice.wav"
  with wave.open(str(path),"wb") as f:
   f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000)
   f.writeframes(b"\x00\x00"*int(length*8000))
  return path
 def test_frames_change_with_real_actor_images(self):
  bg=Image.open(self.background)
  images={key:Image.open(path) for key,path in self.assets.items()}
  a=render_frame(SCENES[0],.2,bg,images,size=(320,180))
  b=render_frame(SCENES[0],4.2,bg,images,size=(320,180))
  self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
  self.assertEqual(a.size,(320,180))
 def test_callout_is_legible_overlay_not_static_card(self):
  scene={**SCENES[0],"callout":"Nuvem de tinta"}
  with Image.open(self.background) as bg:
   layers={name:Image.open(path) for name,path in self.assets.items()}
   try:
    no_caption=render_frame({**scene,"callout":""},1.2,bg,layers,size=(640,360))
    captioned=render_frame(scene,1.2,bg,layers,size=(640,360))
    self.assertIsNotNone(ImageChops.difference(no_caption,captioned).getbbox())
   finally:
    for layer in layers.values():layer.close()
 def test_no_fake_asset_on_missing_image(self):
  with Image.open(self.background) as bg:
   with self.assertRaises(RenderError):
    render_frame(SCENES[0],.3,bg,{})
 @unittest.skipUnless(shutil.which("ffmpeg"),"FFmpeg não está instalado no runner")
 def test_short_real_mp4_and_audio(self):
  scene={**SCENES[0],"duration_target_seconds":2,
         "timeline":[{"at":0,"action":"move","target":"polvo","to_x":.7,"duration":1.5}]}
  wav=self._wav(2)
  result=render_clip(scene,self.background,self.assets,wav,self.root/"scene.mp4",
                     fps=12,size=(320,180))
  self.assertGreater(Path(result["output"]).stat().st_size,1024)
  self.assertEqual(result["frames"],24)
 def test_audio_duration_guard(self):
  with self.assertRaises(RenderError):
   render_clip(SCENES[0],self.background,self.assets,self._wav(.2),
               self.root/"bad.mp4",fps=12,size=(320,180))
if __name__=="__main__":unittest.main()
