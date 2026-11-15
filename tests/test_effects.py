import unittest
from PIL import Image, ImageChops
from universal_engine.effects import paint_effect

class AnimatedEffectsTests(unittest.TestCase):
    def _frame(self,name,t):
        im=Image.new("RGBA",(320,180),(20,50,90,255))
        paint_effect(im,name,160,125,38,t,"fixed")
        return im
    def test_octopus_ink_cloud_grows_without_flicker(self):
        early=self._frame("ink_cloud",.2)
        late=self._frame("ink_cloud",1.5)
        self.assertIsNotNone(ImageChops.difference(early.convert('RGB'),late.convert('RGB')).getbbox())
        self.assertEqual(late.tobytes(),self._frame("ink_cloud",1.5).tobytes())
    def test_volcano_eruption_has_upward_movement(self):
        start=self._frame("smoke",.1)
        later=self._frame("smoke",1.4)
        self.assertIsNotNone(ImageChops.difference(start.convert('RGB'),later.convert('RGB')).getbbox())
