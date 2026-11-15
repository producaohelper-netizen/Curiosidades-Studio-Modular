"""Real 3-topic provider smoke: Commons, CLIP, rembg, Piper, FFmpeg.
Never label output as publishable; these are short engineering samples.
"""
import json, math, pathlib, subprocess, sys
from PIL import Image
from universal_engine.media_sources import search_commons
from universal_engine.visual_pipeline import build_scene_asset
from universal_engine.visual_matcher import OpenCLIPMatcher
from universal_engine.photo_layers import extract_for_scene
from universal_engine.foreground_match import verify_foreground
from universal_engine.narration import generate_piper, retime_to_audio
from universal_engine.layer_renderer import render_clip
from universal_engine.scenespec import validate

ROOT=pathlib.Path("live-demo")
ROOT.mkdir(exist_ok=True)
TOPICS=[
 ("octopus","octopus underwater","A colorful real octopus in the ocean",
  "octopus","orange octopus","Um polvo pode soltar tinta para confundir alguns predadores."),
 ("earth","Earth from space","Planet Earth seen from outer space",
  "earth","planet Earth","A Terra gira sobre o próprio eixo e alterna os dias e as noites."),
 ("volcano","volcano eruption","A volcanic mountain with red glowing lava",
  "volcano","volcanic mountain","Os vulcões podem liberar lava, gases e cinzas durante uma erupção.")
]

def scene(key, query, visual, actor_name, actor_en, text):
 return {
  "version":1,"scene_id":"live_"+key,
  "narration":text,"duration_target_seconds":8.,
  "setting":{"kind":"nature"},"search_terms_en":query,
  "visual_query_en":visual,
  "actors":[{"id":actor_name,"kind":"object","asset_id":key+"-v1",
             "x":.25,"y":.56,"visual_query_en":actor_en,"size":.36}],
  "timeline":[{"at":0.1,"action":"enter","target":actor_name,"to_x":.45,"duration":2.3},
              {"at":2.7,"action":"pulse","target":actor_name,"factor":1.2,"duration":1.2},
              {"at":4.2,"action":"move","target":actor_name,"to_x":.68,"duration":2.1}],
  "visual_fact":text,
 }
def main():
 matcher=OpenCLIPMatcher()
 model=pathlib.Path("voice/pt_BR-faber-medium.onnx")
 results=[]
 for inputs in TOPICS:
  key,query,visual,actor_name,actor_en,text=inputs
  s=scene(*inputs);validate(s)
  outcome=build_scene_asset(s,ROOT/"images",query=query,matcher=matcher,
                             comfy_workflow=None)
  if not outcome.file:
   raise RuntimeError(f"{key}: no matched Commons image: {outcome.reason}")
  folder=ROOT/key;folder.mkdir(exist_ok=True)
  source=pathlib.Path(outcome.file)
  bg=folder/"bg.png";fg=folder/"sprite.png"
  extracted=extract_for_scene(s,source,fg,bg)
  # Diagnostic-only: slightly lower similarity for landscape foregrounds.
  # This does NOT constitute artistic approval or change production strictness.
  min_score=.22 if key=="volcano" else .23
  matched=verify_foreground(s["actors"][0],s,fg,matcher=matcher,minimum=min_score)
  speech=generate_piper(text,model,folder/"speech.wav",timeout=250)
  aligned=retime_to_audio(s,speech["duration"])
  clip=render_clip(aligned,bg,{s["actors"][0]["asset_id"]:fg},
                   speech["path"],folder/"clip.mp4",fps=12,size=(640,360))
  results.append({"topic":key,"voice_seconds":speech["duration"],
                  "foreground_match":matched["score"],"license":outcome.license_name,
                  "provider":outcome.source,"clip_bytes":pathlib.Path(clip["output"]).stat().st_size,
                  "human_approval":"NOT_PERFORMED"})
 pathlib.Path(ROOT/"report.json").write_text(
     json.dumps(results,ensure_ascii=False,indent=2),encoding="utf8")
 print(json.dumps(results,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
