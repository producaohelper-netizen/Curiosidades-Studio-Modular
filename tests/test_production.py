"""Test of six-stage orchestration with fifty distinct planned scenes.

External trends, LLM, video assets, voice and muxing are injected. This is a
CONTRACT test, never evidence of actual YouTube-ready video or real model TTS.
"""
import tempfile
import unittest
import wave
import math
import struct
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw
from universal_engine.production import run, Settings, ProductionError, asset_path
from universal_engine.visual_pipeline import SceneAsset

class PipelineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.settings=Settings(str(self.root),str(self.root/"voice.onnx"),
                               topic="Por que os animais se defendem?")
        (self.root/"voice.onnx").write_bytes(b"placeholder")

    def scene(self,n):
        return {"version":1,"scene_id":f"s{n:03d}",
                "narration":"Os animais usam estratégias para se proteger de predadores.",
                "duration_target_seconds":6.0,
                "setting":{"kind":"forest"},
                "visual_query_en":"Colorful nature animal cartoon action in the forest",
                "actors":[{"id":"animal","kind":"animal","asset_id":"shared_octopus",
                           "x":.15,"y":.5}],
                "timeline":[{"at":0.0,"action":"move","target":"animal",
                             "to_x":.8,"duration":3.0},
                            {"at":3.1,"action":"react","target":"animal",
                             "emotion":"surprised"}],
                "visual_fact":"Animais possuem estratégias defensivas."}

    def fixtures(self):
        root=self.root
        target=asset_path(root/"assets"/"characters","shared_octopus")
        target.parent.mkdir(parents=True,exist_ok=True)
        im=Image.new("RGBA",(64,64),(0,0,0,0))
        ImageDraw.Draw(im).ellipse((10,9,55,60),fill=(255,160,20,255))
        im.save(target)
        background=root/"background.png"
        Image.new("RGB",(1280,720),(45,100,120)).save(background)
        def fake_asset(scene,folder,comfy_workflow=None):
            return SceneAsset(scene["scene_id"],str(background),
                "local-comfyui","Example Artist",True,
                "Requires review","test cartoon","CC BY 4.0",
                "https://creativecommons.org/licenses/by/4.0",
                "https://commons.wikimedia.org/wiki/File:Example")
        def fake_tts(text,model,output,**kw):
            output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
            with wave.open(str(output),"wb") as wav:
                wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(8000)
                wav.writeframes(struct.pack("<h",1200)*6*8000)
            return {"path":str(output),"duration":6.0,"reused":False}
        def fake_clip(scene,bg,sprites,wav,output,**kw):
            output=Path(output);output.write_bytes(b"video mocked")
            return {"output":str(output)}
        return fake_asset,fake_tts,fake_clip

    def test_fifty_scenes_nearly_five_minutes(self):
        asset,tts,clip=self.fixtures()
        def fake_mux(clips, output):
            output.write_bytes(b"assembled video fixture")
            return output
        with patch("universal_engine.production.assert_preflight"):
            result=run(self.settings,
                topic_selector=lambda s:{"title":"Defesas dos animais","trending":False},
                story_writer=lambda topic,llm:{"title":topic,"sections":[],
                    "narration":"Uma fala de teste","words":680},
                planner=lambda text,max_words:{"scenes":[self.scene(i) for i in range(50)]},
                asset_provider=asset,tts=tts,clip_renderer=clip,
                mux=fake_mux,
                probe=lambda video:300.0)
        self.assertEqual(result["status"],"rendered_pending_editorial_review")
        self.assertEqual(result["artistic_approval"],"NOT_PERFORMED")
        self.assertEqual(len(list((self.root/"clips").glob("*.mp4"))),50)
        self.assertEqual(result["duration"],300.0)

    def test_rejects_missing_asset_and_does_not_claim_success(self):
        asset,tts,clip=self.fixtures()
        with patch("universal_engine.production.assert_preflight"):
            with self.assertRaises(ProductionError):
                run(self.settings,
                    topic_selector=lambda s:{"title":"Defesas dos animais"},
                    story_writer=lambda t,l:{"title":t,"sections":[],
                        "narration":"Teste","words":680},
                    planner=lambda text,max_words:{"scenes":[self.scene(i) for i in range(50)]},
                    asset_provider=lambda *a,**kw:SceneAsset(
                        "s000",None,"unavailable","",True,"sem imagem","", "", "", ""),
                    tts=tts,clip_renderer=clip)
        import json
        status=json.loads((self.root/"status.json").read_text())
        self.assertEqual(status["status"],"failed")

if __name__=="__main__":
    unittest.main()
