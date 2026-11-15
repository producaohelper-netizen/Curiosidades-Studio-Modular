import unittest
from pathlib import Path
from universal_engine.style_matcher import cartoon_indices

class TestCartoonStyleGate(unittest.TestCase):
    def test_accepts_cartoon_rejects_photograph(self):
        class Ranker:
            def score(self,text,images):
                if "cartoon" in text.lower(): return [.34,.15]
                return [.16,.35]
        accepted=cartoon_indices(Ranker(),[Path("drawing.png"),Path("photo.png")])
        self.assertEqual(accepted,[0])
    def test_rejects_all_when_only_photos(self):
        class Ranker:
            def score(self,text,images):
                return [.12,.18] if "cartoon" in text.lower() else [.39,.35]
        self.assertEqual(cartoon_indices(Ranker(),[Path("a"),Path("b")]),[])
