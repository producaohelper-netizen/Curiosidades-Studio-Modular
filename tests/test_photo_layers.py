import io
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from universal_engine.photo_layers import photo_layers, extract_for_scene, LayerExtractionError

class PhotoLayerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir=Path(self.temp.name)
        self.photo=self.dir/"original.png"
        Image.new("RGB",(180,120),"steelblue").save(self.photo)
    def remove(self,data):
        out=Image.new("RGBA",(180,120),(0,0,0,0))
        ImageDraw.Draw(out).ellipse((55,20,130,102),fill=(255,150,20,255))
        f=io.BytesIO();out.save(f,"PNG");return f.getvalue()
    def background(self,original,mask):
        self.assertEqual(mask.size,original.size)
        return Image.new("RGB",original.size,"lightblue")
    def test_separate_foreground_background_without_ghosting(self):
        fg=self.dir/"actor.png";bg=self.dir/"background.png"
        result=photo_layers(self.photo,bg,fg,remover=self.remove,
                            background_filler=self.background)
        self.assertTrue(result["review_required"])
        with Image.open(fg) as im:
            self.assertEqual(im.mode,"RGBA")
            self.assertLess(im.width,180,"Crop subject to useful dimensions")
        with Image.open(bg) as im:
            self.assertEqual(im.getpixel((90,60)),(173,215,230))
    def test_requires_single_actor_for_cpu_fallback(self):
        with self.assertRaises(LayerExtractionError):
            extract_for_scene({"actors":[{},{}]},self.photo,self.dir/"a.png",
                              self.dir/"b.png",remover=self.remove)
if __name__=="__main__":
    unittest.main()
