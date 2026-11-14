import json
import tempfile
import unittest
from pathlib import Path
from universal_engine.media_sources import parse_image, search_commons, save_manifest
from universal_engine.visual_matcher import decide, match_scene, export_decision

def record(license_name="CC BY-SA 4.0", title="File:Blue Octopus.jpg"):
    return {"title":title,"imageinfo":[{
      "url":"https://upload.wikimedia.org/example.jpg",
      "thumburl":"https://upload.wikimedia.org/thumb/example.jpg",
      "descriptionurl":"https://commons.wikimedia.org/wiki/File:Blue_Octopus.jpg",
      "extmetadata":{
        "LicenseShortName":{"value":license_name},
        "LicenseUrl":{"value":"https://creativecommons.org/licenses/by-sa/4.0/"},
        "Artist":{"value":"Author Sample"},
        "ImageDescription":{"value":"An octopus <b>in water</b>"}
      }
    }]}

class MediaSourcesTests(unittest.TestCase):
    def test_valid_license_and_attribution(self):
        found=parse_image(record())
        self.assertIsNotNone(found)
        self.assertIn("Author Sample",found.attribution)
        self.assertEqual(found.description,"An octopus  in water")
    def test_reject_restricted_license(self):
        bad=record("CC BY-NC-SA 4.0")
        bad["imageinfo"][0]["extmetadata"]["LicenseUrl"]["value"]="https://creativecommons.org/licenses/by-nc-sa/4.0/"
        self.assertIsNone(parse_image(bad))
    def test_reject_unlicensed_and_bad_urls(self):
        entry=record()
        entry["imageinfo"][0]["extmetadata"]={}
        self.assertIsNone(parse_image(entry))
        entry=record()
        entry["imageinfo"][0]["url"]="file:///home/test.png"
        entry["imageinfo"][0].pop("thumburl")
        self.assertIsNone(parse_image(entry))
    def test_search_api_mock_and_save(self):
        data={"query":{"pages":[record(),record("All Rights Reserved","File:Wrong.jpg")]}}
        result=search_commons("octopus",fetch_json=lambda _:data)
        self.assertEqual(len(result),1)
        with tempfile.TemporaryDirectory() as folder:
            path=save_manifest(result,Path(folder)/"manifest.json")
            saved=json.loads(path.read_text(encoding="utf8"))
            self.assertEqual(len(saved["images"]),1)
            self.assertTrue(saved["needs_individual_license_review"])
    def test_select_high_similarity(self):
        c=parse_image(record())
        self.assertEqual(decide([c],[.33]).status,"selected")
        self.assertEqual(decide([c],[.11]).status,"review_required")
        self.assertEqual(decide([],[]).status,"no_candidates")
    def test_ambiguous_images_blocked(self):
        a,b=parse_image(record()),parse_image(record(title="File:Second.jpg"))
        self.assertEqual(decide([a,b],[.36,.355]).status,"review_required")
    def test_scene_with_stub_embeddings(self):
        class Stub:
            def score(self,prompt,images):
                self.last_prompt=prompt
                return [.4]
        candidate=parse_image(record())
        matcher=Stub()
        dec=match_scene({"visual_query_en":"An orange octopus underwater spraying dark ink"},
                        [candidate],["/not/downloaded/for/mock.jpg"],matcher)
        self.assertEqual(dec.status,"selected")
        with tempfile.TemporaryDirectory() as folder:
            path=export_decision("scene12",dec,Path(folder)/"decision.json")
            self.assertTrue(path.is_file())
        with self.assertRaises(ValueError):
            match_scene({"visual_query_en":"polvo"},[candidate],["x.png"],matcher)
if __name__=="__main__":
    unittest.main()
