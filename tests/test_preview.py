import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageChops
from test_scenespec import SCENES
from universal_engine.preview import render, contact_sheet

class TestUniversalVisualPreview(unittest.TestCase):
 def test_all_subjects_are_drawable(self):
  for scene in SCENES:
   with self.subTest(scene=scene["scene_id"]):
    start=render(scene,0.1)
    end=render(scene,scene["duration_target_seconds"]*.7)
    self.assertEqual(start.size,(960,540))
    self.assertIsNotNone(ImageChops.difference(start,end).getbbox(),"Frames nao mudaram!")
 def test_contact_sheet_nine_frames(self):
  with tempfile.TemporaryDirectory() as folder:
   for scene in SCENES:
    path=contact_sheet(scene,Path(folder)/(scene["scene_id"]+".jpg"))
    self.assertTrue(path.exists())
    with Image.open(path) as image:self.assertEqual(image.size,(1440,810))
