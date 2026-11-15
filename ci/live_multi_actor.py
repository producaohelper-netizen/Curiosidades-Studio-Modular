"""Real two-character illustrated action, with licensed independent SVG/PNG assets.
No generated shapes, no photographic substitutes, no fake narration.
"""
import json
from pathlib import Path
from universal_engine.multiactor import illustrated_actors
from universal_engine.visual_pipeline import build_scene_asset
from universal_engine.narration import generate_piper, retime_to_audio
from universal_engine.layer_renderer import render_clip
from universal_engine.scenespec import validate

ROOT=Path("real-multi-actor")
ROOT.mkdir(exist_ok=True)
scene={
 "version":1,"scene_id":"octopus_vs_shark",
 "narration":(
    "Olha só! O tubarão se aproxima, e o polvo percebe o perigo. "
    "Em um piscar de olhos, ele solta uma nuvem escura de tinta. "
    "O tubarão fica confuso, e o polvo aproveita para fugir!"),
 "duration_target_seconds":13,
 "setting":{"kind":"underwater"},
 "visual_style":"cartoon",
 "visual_query_en":"cartoon octopus escapes shark by releasing ink underwater",
 "visual_fact":"Alguns polvos podem liberar tinta para confundir predadores.",
 "callout":"FUGA SURPRESA",
 "actors":[
  {"id":"octopus","kind":"animal","asset_id":"red-octopus-v1","x":.23,"y":.52,
   "size":.26,"visual_query_en":"red octopus with curling eight tentacles",
   "search_terms_en":"octopus"},
  {"id":"shark","kind":"animal","asset_id":"blue-shark-v1","x":.90,"y":.55,
   "size":.30,"visual_query_en":"blue shark with fins and teeth cartoon",
   "search_terms_en":"shark"}
 ],
 "timeline":[
  {"at":.1,"action":"enter","target":"octopus","to_x":.34,"duration":.45},
  {"at":.2,"action":"enter","target":"shark","to_x":.79,"duration":.45},
  {"at":1.0,"action":"approach","target":"shark","towards":"octopus","duration":1.5},
  {"at":2.8,"action":"react","target":"octopus","emotion":"surprised"},
  {"at":4.0,"action":"emit_particles","target":"octopus","effect":"ink_cloud"},
  {"at":5.5,"action":"escape","target":"octopus","to_x":.05,
   "to_y":.42,"duration":2.4},
  {"at":5.8,"action":"react","target":"shark","emotion":"confused"}
 ]
}
validate(scene)
background,sprites,manifest=illustrated_actors(
    scene,ROOT/"assets",provider=build_scene_asset)
model=Path("voice/pt_BR-faber-medium.onnx")
audio=generate_piper(scene["narration"],model,ROOT/"voice.wav",timeout=240)
aligned=retime_to_audio(scene,audio["duration"])
clip=render_clip(aligned,background,sprites,audio["path"],
                 ROOT/"clip.mp4",fps=24,size=(960,540))
report={
  "subject":"octopus and shark interaction",
  "video":clip["output"],"duration_seconds":clip["duration"],
  "individual_asset_credits":manifest.original_url,
  "transparent_assets":list(sprites),
  "narration":"Piper pt-BR real",
  "technical_rendered":True,"artistic_approval":"NOT_PERFORMED"}
(ROOT/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),
                               encoding="utf8")
print(json.dumps(report,indent=2,ensure_ascii=False))
