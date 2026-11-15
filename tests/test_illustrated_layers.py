import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from universal_engine.illustrated_layers import (
    has_alpha,alpha_sprite,create_background,IllustratedLayerError
)

class IllustratedLayersTests(unittest.TestCase):
    def test_transparent_vector_sprite_and_original_background(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/"svg_thumbnail.png";dest=root/"actor.png"
            picture=Image.new("RGBA",(240,150),(0,0,0,0))
            painter=ImageDraw.Draw(picture)
            painter.ellipse((70,20,175,135),fill="#ff9346")
            picture.save(src)
            self.assertTrue(has_alpha(src))
            alpha_sprite(src,dest)
            with Image.open(dest) as im:
                self.assertLess(im.width,src.stat().st_size)
                self.assertLess(im.width,240)
                self.assertEqual(im.mode,"RGBA")
            bg=create_background("underwater",root/"bg.png",size=(320,180),
                                 identity="octopus-1")
            with Image.open(bg) as im:
                self.assertEqual(im.size,(320,180))
                self.assertEqual(im.mode,"RGB")
    def test_deterministic_backgrounds_across_restarts(self):
        with tempfile.TemporaryDirectory() as d:
            first=create_background("space",Path(d)/"one.png",
                                    size=(320,180),identity="earth")
            second=create_background("space",Path(d)/"two.png",
                                     size=(320,180),identity="earth")
            self.assertEqual(first.read_bytes(),second.read_bytes())
    def test_opaque_photographs_do_not_masquerade_as_sprites(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"photo.png";Image.new("RGB",(100,100),"red").save(src)
            self.assertFalse(has_alpha(src))
            with self.assertRaises(IllustratedLayerError):
                alpha_sprite(src,Path(d)/"new.png")
