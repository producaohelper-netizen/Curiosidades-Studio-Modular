import unittest
from PIL import Image,ImageChops
from universal_engine.environment_motion import draw_environment

class EnvironmentMotionTests(unittest.TestCase):
    def test_motion_for_four_different_settings(self):
        for setting in ("underwater","forest","space","volcanic"):
            with self.subTest(setting=setting):
                def make(t):
                    im=Image.new("RGBA",(320,180),(20,50,80,255))
                    return draw_environment(im,setting,t,"scene-01")
                start=make(.2)
                later=make(3.1)
                self.assertIsNotNone(ImageChops.difference(start,later).getbbox())
                self.assertEqual(make(3.1).tobytes(),later.tobytes())
    def test_unknown_setting_never_changes_frame(self):
        base=Image.new("RGBA",(320,180),(100,50,20,255))
        out=draw_environment(base.copy(),"unknown",2,"scene")
        self.assertEqual(out.tobytes(),base.tobytes())
    def test_nonfinite_time_rejected(self):
        with self.assertRaises(ValueError):
            draw_environment(Image.new("RGBA",(100,100)),"space",float("nan"))
