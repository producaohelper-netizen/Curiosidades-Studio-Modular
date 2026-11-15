import tempfile
import unittest
from pathlib import Path
from universal_engine.foreground_match import verify_foreground, ForegroundMismatch

class ForegroundMatchTests(unittest.TestCase):
    def setUp(self):
        self.actor={"id":"polvo","kind":"animal","visual_query_en":"orange octopus"}
        self.scene={"scene_id":"ocean1","search_terms_en":"octopus shark ocean"}
    def test_correct_subject(self):
        class GoodMatcher:
            def score(self,text,images):
                self.assertion = text
                return [.37]
        v=verify_foreground(self.actor,self.scene,Path("test.png"),matcher=GoodMatcher())
        self.assertGreater(v["score"],.23)
        self.assertIn("octopus",v["subject_text"])
    def test_cartoon_style_uses_illustration_prompt(self):
        prompts=[]
        class Model:
            def score(self,text,images):
                prompts.append(text)
                return [.45]
        scene={**self.scene,"visual_style":"cartoon"}
        verify_foreground(self.actor,scene,Path("sprite.png"),matcher=Model())
        self.assertIn("2D cartoon illustration",prompts[0])
        self.assertNotIn("photograph",prompts[0])
    def test_reject_wrong_subject(self):
        class WrongMatcher:
            def score(self,text,images):return [.04]
        with self.assertRaises(ForegroundMismatch):
            verify_foreground(self.actor,self.scene,Path("not-octopus.png"),
                              matcher=WrongMatcher())
    def test_requires_visual_description(self):
        with self.assertRaises(ForegroundMismatch):
            verify_foreground({}, {}, Path("img.png"),matcher=object())
