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
from universal_engine.production import run, Settings, ProductionError, asset_path, prepare_scene_assets
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
            target=asset_path(Path(folder).parent/"characters","shared_octopus")
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():
                im=Image.new("RGBA",(64,64),(0,0,0,0))
                ImageDraw.Draw(im).ellipse((10,9,55,60),fill=(255,160,20,255))
                im.save(target)
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

    def test_vector_ollama_fallback_without_images_or_gpu(self):
        self.settings.vector_fallback=True
        scene=self.scene(0)
        scene["visual_style"]="cartoon"
        def no_assets(*args,**kwargs):
            return SceneAsset("s000",None,"unavailable","",True,
                              "Sem banco de imagens","", "", "", "")
        def fake_vector(actor,out,model):
            out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
            image=Image.new("RGBA",(80,80),(0,0,0,0))
            ImageDraw.Draw(image).ellipse((9,8,70,72),fill=(255,140,33,255))
            image.save(out)
            return out
        with patch("universal_engine.production.generate_actor",side_effect=fake_vector):
            with patch("universal_engine.production.verify_foreground",
                       return_value={"score":.29}):
                bg,layers,manifest=prepare_scene_assets(scene,self.root/"asset_test",
                                  self.settings,get_asset=no_assets)
        self.assertTrue(bg.is_file())
        self.assertEqual(manifest.source,"local-ollama-vector")
        self.assertTrue(layers["shared_octopus"].is_file())
        self.assertTrue(manifest.review_required)
    def test_fifty_scenes_nearly_five_minutes(self):
        asset,tts,clip=self.fixtures()
        def fake_mux(clips, output):
            output.write_bytes(b"assembled video fixture")
            return output
        with patch("universal_engine.production.assert_preflight"):
            result=run(self.settings,
                topic_selector=lambda s:{"title":"Defesas dos animais","trending":False},
                story_writer=lambda topic,llm:{"title":topic,"sections":[],
                    "narration":" ".join(self.scene(i)["narration"] for i in range(50)),"words":680},
                planner=lambda text,max_words:{"scenes":[self.scene(i) for i in range(50)]},
                asset_provider=asset,tts=tts,clip_renderer=clip,
                mux=fake_mux,
                probe=lambda video:300.0)
        self.assertEqual(result["status"],"rendered_pending_editorial_review")
        self.assertEqual(result["artistic_approval"],"NOT_PERFORMED")
        self.assertEqual(len(list(Path(result["workspace"]).joinpath("clips").glob("*.mp4"))),50)
        self.assertEqual(result["duration"],300.0)

    def test_voice_calibrated_before_visual_render(self):
        asset,unused_tts,clip=self.fixtures()
        calls=[]
        def variable_tts(text,model,wav,**kwargs):
            scale=float(kwargs.get("length_scale",1))
            calls.append(scale)
            return {"path":str(wav),"duration":5.0*scale}
        def fake_mux(clips,output):
            output.write_bytes(b"assembled mock")
            return output
        with patch("universal_engine.production.assert_preflight"):
            result=run(self.settings,
                topic_selector=lambda s:{"title":"Defesas dos animais","trending":False},
                story_writer=lambda t,l:{"title":t,"sections":[],
                    "narration":" ".join(self.scene(i)["narration"] for i in range(50)),"words":680},
                planner=lambda text,max_words:{"scenes":[self.scene(i) for i in range(50)]},
                asset_provider=asset,tts=variable_tts,clip_renderer=clip,
                mux=fake_mux,probe=lambda video:300.0)
        self.assertEqual(result["status"],"rendered_pending_editorial_review")
        self.assertEqual(len(calls),100)
        self.assertAlmostEqual(calls[0],1.0)
        self.assertAlmostEqual(calls[50],1.2)
        stages=[r["stage"] for r in result["stages"]]
        self.assertLess(stages.index("voice_duration_checked"),
                        stages.index("scene_render"))
    def test_rejects_missing_asset_and_does_not_claim_success(self):
        self.settings.vector_fallback=False
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
        status=json.loads(next((self.root/"episodes").iterdir()).joinpath("status.json").read_text())
        self.assertEqual(status["status"],"failed")

if __name__=="__main__":
    unittest.main()
