import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from universal_engine.multiactor import illustrated_actors, MultiActorError
from universal_engine.visual_pipeline import SceneAsset

class MultiActorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.fake_image=self.root/"subject.png"
  im=Image.new("RGBA",(240,180),(0,0,0,0))
  ImageDraw.Draw(im).ellipse((50,20,190,160),fill=(245,100,45,255))
  im.save(self.fake_image)
  self.scenes=[{
   "scene_id":"ocean_1","setting":{"kind":"underwater"},
   "visual_query_en":"octopus escapes predator",
   "actors":[
     {"id":"octopus","asset_id":"octopus-stable","kind":"animal",
      "visual_query_en":"colorful illustration orange octopus"},
     {"id":"predator","asset_id":"shark-stable","kind":"animal",
      "visual_query_en":"blue cartoon shark with teeth"}]}]
  self.calls=[]
 def provider(self,scene,root,comfy_workflow=None):
  self.calls.append(scene["scene_id"])
  return SceneAsset(scene["scene_id"],str(self.fake_image),
                    "Wikimedia Commons","Illustration Author",True,
                    "illustration",scene["visual_query_en"],
                    "CC BY 4.0","https://creativecommons.org/licenses/by/4.0/",
                    "https://commons.wikimedia.org/wiki/File:Example.svg","cartoon")
 def test_two_actors_individually_selected_and_cached(self):
  bg,actors,meta=illustrated_actors(self.scenes[0],self.root/"work",
                                   provider=self.provider)
  self.assertTrue(bg.is_file())
  self.assertEqual(set(actors),{"octopus-stable","shark-stable"})
  self.assertEqual(len(self.calls),2)
  self.assertTrue(Path(meta.original_url).is_file())
  self.scenes[0]["scene_id"]="ocean_2"
  illustrated_actors(self.scenes[0],self.root/"work",provider=self.provider)
  self.assertEqual(len(self.calls),2,"Repeated characters must use cached drawings")
 def test_missing_alpha_is_rejected(self):
  Image.new("RGB",(240,180),"red").save(self.fake_image)
  with self.assertRaises(MultiActorError):
   illustrated_actors(self.scenes[0],self.root/"noalpha",provider=self.provider)
 def test_missing_licence_is_rejected(self):
  def bad(*args,**kwargs):
   r=self.provider(*args,**kwargs)
   r.license_name=""
   return r
  with self.assertRaises(MultiActorError):
   illustrated_actors(self.scenes[0],self.root/"nolicence",provider=bad)
