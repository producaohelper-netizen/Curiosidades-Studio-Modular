import tempfile
import unittest
from pathlib import Path
from PIL import Image
from universal_engine.visual_pipeline import build_scene_asset, AssetPipelineError
from universal_engine.media_sources import MediaCandidate

SCENE={"scene_id":"s014","visual_query_en":"Cartoon octopus squirting ink as a shark approaches",
       "narration":"O polvo solta tinta para fugir."}
ITEM=MediaCandidate("File:Octopus.jpg","https://upload.wikimedia.org/o.jpg",
                    "https://commons.wikimedia.org/wiki/File:Octopus.jpg",
                    "CC BY 4.0","https://creativecommons.org/licenses/by/4.0",
                    "Photographer A","Octopus","Octopus; Photographer A; CC BY 4.0")

class PipelineTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
 def fake_download(self,record,path):
  im=Image.new("RGB",(64,64),"navy")
  im.save(path)
  return Path(path)
 def test_select_licensed_match_and_save_manifest(self):
  class Match:
   def score(self,query,files):return [.42]
  r=build_scene_asset(SCENE,self.temp.name,matcher=Match(),
                      commons_search=lambda query,limit:[ITEM],
                      downloader=self.fake_download)
  self.assertEqual(r.source,"Wikimedia Commons")
  self.assertTrue(r.review_required)
  self.assertTrue(Path(r.file).is_file())
  self.assertIn("Photographer A",r.attribution)
  self.assertTrue((Path(self.temp.name)/"s014"/"asset.json").exists())
 def test_reject_false_match_when_generator_missing(self):
  class Match:
   def score(self,query,files):return [.05]
  r=build_scene_asset(SCENE,self.temp.name,matcher=Match(),
                      commons_search=lambda query,limit:[ITEM],
                      downloader=self.fake_download)
  self.assertIsNone(r.file)
  self.assertEqual(r.source,"unavailable")
  self.assertTrue(r.review_required)
 def test_local_generation_only_after_mismatch(self):
  class Match:
   def score(self,query,files):return [.02]
  class FakeResult:
   def __init__(self,file):self.file=str(file)
  def fake_gen(prompt,workflow,file):
   self.assertEqual(workflow,"fake_workflow.json")
   Image.new("RGB",(40,40),"cyan").save(file)
   return FakeResult(file)
  r=build_scene_asset(SCENE,self.temp.name,matcher=Match(),
                      commons_search=lambda query,limit:[ITEM],
                      downloader=self.fake_download,
                      comfy_workflow="fake_workflow.json",generator=fake_gen)
  self.assertEqual(r.source,"local-comfyui")
  self.assertTrue(r.review_required)
  self.assertTrue(Path(r.file).exists())
 def test_no_unrelated_image_substitution(self):
  r=build_scene_asset(SCENE,self.temp.name,
                      commons_search=lambda query,limit:[])
  self.assertIsNone(r.file)
  self.assertEqual(r.source,"unavailable")
 def test_scene_requires_prompt(self):
  with self.assertRaises(AssetPipelineError):
   build_scene_asset({"scene_id":"bad"},self.temp.name)
if __name__=="__main__":
 unittest.main()
