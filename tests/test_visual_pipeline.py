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
 def test_cached_photo_never_reused_in_cartoon_mode(self):
  # Earlier photo acceptance must not bypass the new style gate.
  class Match:
   def score(self,query,files):
    if "flat two dimensional cartoon" in query:return [.08]
    if "documentary photograph" in query:return [.44]
    return [.41]
  def only_first(query,limit):return [ITEM]
  photo_scene={**SCENE,"visual_style":"photo"}
  cartoon_scene={**SCENE,"visual_style":"cartoon"}
  first=build_scene_asset(photo_scene,self.temp.name,matcher=Match(),
                          commons_search=only_first,downloader=self.fake_download)
  self.assertIsNotNone(first.file)
  second=build_scene_asset(cartoon_scene,self.temp.name,matcher=Match(),
                           commons_search=only_first,downloader=self.fake_download)
  self.assertIsNone(second.file,"Foto antiga não pode passar por cartoon")
 def test_character_search_excludes_anatomy_diagrams(self):
  anatomical=MediaCandidate("File:Shark Anatomy.svg",
      "https://upload.wikimedia.org/shark-anatomy.png",
      "https://commons.wikimedia.org/wiki/File:Shark_Anatomy.svg",
      "CC BY 4.0","https://creativecommons.org/licenses/by/4.0",
      "Author","Labeled anatomical diagram of shark fins",
      "Author CC BY 4.0")
  illustration=MediaCandidate("File:Blue_shark_cartoon.svg",
      "https://upload.wikimedia.org/shark-cartoon.png",
      "https://commons.wikimedia.org/wiki/File:Blue_shark_cartoon.svg",
      "CC BY 4.0","https://creativecommons.org/licenses/by/4.0",
      "Artist","Cute illustrated shark with no labels",
      "Artist CC BY 4.0")
  class Ranker:
   def score(self,query,files):
    if "flat two dimensional cartoon" in query:return [.49]
    if "documentary photograph" in query:return [.16]
    return [.48]
  scene={**SCENE,"scene_id":"shark_cartoon","asset_purpose":"actor",
         "visual_style":"cartoon"}
  chosen=build_scene_asset(scene,self.temp.name,matcher=Ranker(),
      commons_search=lambda query,limit:[anatomical,illustration],
      downloader=self.fake_download)
  self.assertEqual(chosen.original_url,illustration.page_url)
 def test_comfy_prompt_requires_cartoon_style(self):
  class FalseMatcher:
   def score(self,query,files):return [.01]
  class Result:
   def __init__(self,file):self.file=str(file)
  observed=[]
  def fake_gen(prompt,workflow,file):
   observed.append(prompt)
   Image.new("RGB",(120,100),"orange").save(file)
   return Result(file)
  scene={**SCENE,"visual_style":"cartoon"}
  r=build_scene_asset(scene,self.temp.name,matcher=FalseMatcher(),
      commons_search=lambda q,limit:[],comfy_workflow="workflow.json",
      generator=fake_gen)
  self.assertEqual(r.visual_style,"cartoon")
  self.assertIn("NOT a photograph",observed[0])

if __name__=="__main__":
 unittest.main()
