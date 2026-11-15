import io
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from universal_engine.sprite_factory import (
    SpriteError, produce_sprite, assert_cutout, sprite_filename,
)

class SpriteFactoryTests(unittest.TestCase):
    def test_cache_preserves_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            calls=[]
            actor={"id":"octopus","kind":"animal","asset_id":"octopus_01",
                   "display_name":"orange cartoon octopus"}
            def fake_generate(prompt,workflow,destination,seed=None):
                calls.append(seed)
                Image.new("RGB",(128,128),"white").save(destination)
            def fake_remove(raw):
                image=Image.new("RGBA",(128,128),(0,0,0,0))
                d=ImageDraw.Draw(image)
                d.ellipse((29,17,98,111),fill=(242,132,64,255))
                out=io.BytesIO();image.save(out,"PNG");return out.getvalue()
            first=produce_sprite(actor,root,"workflow.json",generator=fake_generate,
                                 remover=fake_remove)
            second=produce_sprite(actor,root,"workflow.json",generator=fake_generate,
                                  remover=fake_remove)
            self.assertEqual(first,second)
            self.assertEqual(len(calls),1,"Repeated assets must not be regenerated")
            self.assertTrue(json.loads(first.with_suffix(".json").read_text())["requires_visual_review"])
    def test_reject_solid_image(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"opaque.png"
            Image.new("RGBA",(80,80),(255,0,0,255)).save(p)
            with self.assertRaises(SpriteError): assert_cutout(p)
    def test_reject_empty_alpha(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"empty.png"
            Image.new("RGBA",(80,80),(255,0,0,0)).save(p)
            with self.assertRaises(SpriteError): assert_cutout(p)
    def test_reject_if_no_workflow(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SpriteError):
                produce_sprite({"id":"moon","kind":"planet","asset_id":"moon_01"},d,None)
    def test_stable_safe_filename(self):
        s=sprite_filename("../outside")
        self.assertNotIn("/",s)
        self.assertTrue(s.endswith(".png"))

if __name__=="__main__":
    unittest.main()
