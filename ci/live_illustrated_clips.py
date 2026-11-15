"""Real illustrated two-topic sample, no mocked audio or render path.

Wikimedia transparent drawings + OpenCLIP + moving illustrated background +
Piper pt-BR + generic animation SceneSpec + FFmpeg. Short *diagnostic*
clips, never mark artistic review as passed without human inspection.
"""
from pathlib import Path
import json
from PIL import Image
from universal_engine.visual_pipeline import build_scene_asset
from universal_engine.visual_matcher import OpenCLIPMatcher
from universal_engine.illustrated_layers import alpha_sprite,create_background,has_alpha
from universal_engine.narration import generate_piper,retime_to_audio
from universal_engine.layer_renderer import render_clip
from universal_engine.scenespec import validate

ROOT=Path("real-illustrated-test")
ROOT.mkdir(exist_ok=True)
voice=Path("voice/pt_BR-faber-medium.onnx")
specs=[
 {"version":1,"scene_id":"octopus","narration":
  "Imagine um polvo passeando no fundo do mar. De repente aparece um predador! "
  "O polvo solta uma nuvem de tinta e dispara para se esconder. Que esperteza!",
  "duration_target_seconds":11,
  "setting":{"kind":"underwater"},"visual_style":"cartoon",
  "visual_query_en":"A recognizable red octopus in a clean hand-drawn underwater illustration",
  "search_terms_en":"octopus",
  "visual_fact":"Um polvo pode liberar tinta para confundir predadores.",
  "callout":"NUVEM DE TINTA",
  "actors":[{"id":"octopus","asset_id":"red-octopus","kind":"animal",
             "x":.22,"y":.53,"size":.35,
             "visual_query_en":"red octopus with visible tentacles and head"}],
  "timeline":[{"at":.3,"action":"enter","target":"octopus","duration":2,"to_x":.46},
              {"at":3.4,"action":"react","target":"octopus","emotion":"surprised"},
              {"at":4.5,"action":"emit_particles","target":"octopus","effect":"ink_cloud"},
              {"at":7.1,"action":"escape","target":"octopus","duration":2.6,
               "to_x":.12,"to_y":.48}]},
 {"version":1,"scene_id":"volcano","narration":
  "Um vulcão parece uma montanha bem calma. Só que lá dentro existe rocha derretida, "
  "chamada magma. Quando ela chega à superfície, vira lava e pode escorrer pelas encostas.",
  "duration_target_seconds":11,
  "setting":{"kind":"volcanic"},"visual_style":"cartoon",
  "visual_query_en":"A vivid drawing of an erupting volcano with a recognizable mountain shape",
  "search_terms_en":"volcano",
  "visual_fact":"A lava é magma que chega à superfície.",
  "callout":"LAVA",
  "actors":[{"id":"volcano","asset_id":"erupting-volcano","kind":"object",
             "x":.5,"y":.54,"size":.5,
             "visual_query_en":"erupting volcanic mountain with lava and smoke"}],
  "timeline":[{"at":.2,"action":"enter","target":"volcano","duration":2.0,
               "to_x":.5},
              {"at":3.6,"action":"pulse","target":"volcano","factor":1.08,"duration":2.2},
              {"at":5.7,"action":"emit_particles","target":"volcano","effect":"lava_smoke"}]}
]
matcher=OpenCLIPMatcher()
results=[]
for scene in specs:
    validate(scene)
    name=scene["scene_id"]
    target=ROOT/name;target.mkdir(exist_ok=True)
    asset=build_scene_asset(scene,target/"search",matcher=matcher)
    if not asset.file or not has_alpha(asset.file):
        raise RuntimeError(f"{name}: clean licensed transparent illustration missing: {asset.reason}")
    sprite=alpha_sprite(asset.file,target/"sprite.png")
    bg=create_background(scene["setting"]["kind"],target/"background.png",
                         size=(960,540),identity=name)
    speech=generate_piper(scene["narration"],voice,target/"voice.wav",timeout=240)
    aligned=retime_to_audio(scene,speech["duration"])
    video=render_clip(aligned,bg,{scene["actors"][0]["asset_id"]:sprite},
                      speech["path"],target/"clip.mp4",fps=24,size=(960,540))
    results.append({"topic":name,"duration":video["duration"],
                    "source":asset.original_url,
                    "license":asset.license_name,
                    "video":video["output"],
                    "subject_is_recognizable":"REQUIRES_VISUAL_REVIEW",
                    "artistic_approval":"NOT_PERFORMED"})
    print(json.dumps(results[-1],ensure_ascii=False),flush=True)
(ROOT/"report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),
                                encoding="utf8")
