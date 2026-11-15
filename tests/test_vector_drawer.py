import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from universal_engine.vector_drawer import (
    VectorArtError, rasterize, generate_actor, validate_art, normalize_simple_shapes
)

def drawing():
    elements=[
        {"shape":"ellipse","bbox":[50,80,445,445],
         "fill":"#e75c32","stroke":"#192940","width":10},
        {"shape":"ellipse","bbox":[165,160,230,250],"fill":"#ffffff"},
        {"shape":"ellipse","bbox":[300,160,365,250],"fill":"#ffffff"},
        {"shape":"ellipse","bbox":[188,186,220,232],"fill":"#182436"},
        {"shape":"ellipse","bbox":[323,186,355,232],"fill":"#182436"},
        {"shape":"arc","bbox":[202,230,345,355],"start":0,"end":180,
         "stroke":"#182436","width":8},
        {"shape":"polygon","points":[[70,350],[95,400],[180,380]],
         "fill":"#ff955c","stroke":"#17233e","width":8},
        {"shape":"ellipse","bbox":[280,288,306,309],"fill":"#f3ad72"},
    ]
    return {"elements":elements}

class VectorDrawingTests(unittest.TestCase):
    def test_illustration_is_transparent_and_reproducible(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"a.png";b=Path(d)/"b.png"
            rasterize(drawing(),a);rasterize(drawing(),b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with Image.open(a) as image:
                self.assertEqual(image.mode,"RGBA")
                self.assertLess(image.getchannel("A").getextrema()[0],255)
                self.assertGreater(image.getchannel("A").getextrema()[1],0)
    def test_local_ollama_json_is_never_executed(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def ai(payload):
                calls.append(payload["model"])
                return {"response":json.dumps(drawing())}
            actor={"id":"polvo","kind":"animal","asset_id":"octopus-A",
                   "visual_query_en":"orange cartoon octopus with eyes"}
            dest=Path(d)/"actor.png"
            generate_actor(actor,dest,requester=ai)
            generate_actor(actor,dest,requester=ai)
            self.assertEqual(calls,["qwen2.5:7b"])
            self.assertTrue(dest.with_suffix(".json").is_file())
    def test_strict_short_model_forms_allow_inverted_bbox(self):
        raw={"e":[{"t":"ellipse","b":[400,390,80,90],
                   "f":"#FFCC33","s":"#102030","w":4}
                  for _ in range(8)]}
        result=normalize_simple_shapes(raw)
        self.assertEqual(result["elements"][0]["bbox"],[80,90,400,390])
        with tempfile.TemporaryDirectory() as folder:
            path=rasterize(result,Path(folder)/"normalized.png")
            self.assertTrue(path.is_file())
    def test_clip_small_overshoot_from_ollama(self):
        raw={"e":[{"t":"ellipse","b":[-8,40,516,490],
                   "f":"#66BBCC","s":"#102030","w":3} for _ in range(8)]}
        obj=normalize_simple_shapes(raw)
        self.assertEqual(obj["elements"][0]["bbox"],[0.0,40,512.0,490])
    def test_reject_extreme_coords_even_if_numbers(self):
        raw={"e":[{"t":"ellipse","b":[0,0,100,100],
                   "f":"#66BBCC","s":"#102030","w":3} for _ in range(8)]}
        raw["e"][0]["b"][0]=-999
        with self.assertRaises(VectorArtError):
            normalize_simple_shapes(raw)
    def test_invalid_optional_coordinates_are_never_faked(self):
        raw={"e":[{"t":"ellipse","b":[0,0,100,100],
                   "f":"#FFCC33","s":"#102030","w":4}
                  for _ in range(8)]}
        raw["e"][2].pop("b")
        with self.assertRaises(VectorArtError):normalize_simple_shapes(raw)
    def test_model_short_schema_conversion(self):
        response={"e":[{"t":"ellipse","b":[100,80,320,280],
                        "f":"#FFCC33","s":"#102030","w":4}
                       for _ in range(8)]}
        def fake_ai(payload):
            self.assertEqual(payload["format"]["properties"]["e"]["minItems"],8)
            required=payload["format"]["properties"]["e"]["items"]["required"]
            self.assertEqual(set(required),{"t","b","f","s","w"})
            return {"response":json.dumps(response)}
        from universal_engine.vector_drawer import local_instructions
        parsed,_=local_instructions({"id":"planet earth","kind":"planet"},
                                    requester=fake_ai)
        self.assertEqual(len(parsed["elements"]),8)
    def test_invalid_first_attempt_gets_correction_prompt(self):
        from universal_engine.vector_drawer import local_instructions
        calls=[]
        bad={"e":[{"t":"ellipse","b":[90,90,90,90],
                   "f":"#F0C050","s":"#111A22","w":3} for _ in range(8)]}
        good={"e":[{"t":"ellipse","b":[80,80,330,300],
                    "f":"#F0C050","s":"#111A22","w":3} for _ in range(8)]}
        def fake(payload):
            calls.append(payload["prompt"])
            return {"response":json.dumps(good if len(calls)>1 else bad)}
        result,_=local_instructions({"id":"planet earth","kind":"planet"},requester=fake)
        self.assertEqual(len(result["elements"]),8)
        self.assertEqual(len(calls),2)
        self.assertIn("CORRIJA O DESENHO",calls[1])
    def test_all_invalid_attempts_raise_error(self):
        from universal_engine.vector_drawer import local_instructions
        calls=[]
        def bad_response(payload):
            calls.append(payload["prompt"])
            return {"response":json.dumps({"e":[{"t":"ellipse","b":[0,0,0,0],
                "f":"#F0C050","s":"#111A22","w":3} for _ in range(8)]})}
        with self.assertRaises(VectorArtError):
            local_instructions({"id":"octopus","kind":"animal"},requester=bad_response)
        self.assertEqual(len(calls),3)
    def test_disallow_unrecognized_and_unsafe_instructions(self):
        bad=drawing()
        bad["elements"][0]["shape"]="script"
        with self.assertRaises(VectorArtError): validate_art(bad)
        bad=drawing();bad["elements"][0]["fill"]="url(https://unsafe.example)"
        with self.assertRaises(VectorArtError): validate_art(bad)
        bad=drawing();bad["elements"][0]["bbox"]=[0,0,99999999,99999999]
        with self.assertRaises(VectorArtError): validate_art(bad)
