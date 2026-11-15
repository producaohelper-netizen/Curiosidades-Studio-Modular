import unittest
from pathlib import Path
from universal_engine.style_matcher import cartoon_indices, actor_indices

class TestCartoonStyleGate(unittest.TestCase):
    def test_accepts_cartoon_rejects_photograph(self):
        class Ranker:
            def score(self,text,images):
                if "cartoon" in text.lower(): return [.34,.15]
                return [.16,.35]
        accepted=cartoon_indices(Ranker(),[Path("drawing.png"),Path("photo.png")])
        self.assertEqual(accepted,[0])
    def test_illustrated_character_filters_scientific_diagram(self):
        class Matcher:
            def score(self,text,images):
                if "scientific anatomy diagram" in text:return [.38,.12]
                if "single complete recognizable cute cartoon" in text:return [.19,.51]
                raise AssertionError(text)
        indexes=actor_indices(Matcher(),[Path("anatomy.png"),Path("character.png")])
        self.assertEqual(indexes,[1])
    def test_no_suitable_actor_is_not_auto_approved(self):
        class Matcher:
            def score(self,text,images):
                return [.11] if "single complete" in text else [.39]
        self.assertEqual(actor_indices(Matcher(),[Path("diagram.png")]),[])
    def test_rejects_all_when_only_photos(self):
        class Ranker:
            def score(self,text,images):
                return [.12,.18] if "cartoon" in text.lower() else [.39,.35]
        self.assertEqual(cartoon_indices(Ranker(),[Path("a"),Path("b")]),[])
