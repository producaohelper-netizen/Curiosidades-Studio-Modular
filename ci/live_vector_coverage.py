"""Real cartoon-asset coverage check across three unrelated topics.

Does not silently replace cartoons with photographs. Each asset includes
licensing metadata and has a manual artistic review flag.
"""
from pathlib import Path
import json
from PIL import Image
from universal_engine.visual_pipeline import build_scene_asset
from universal_engine.visual_matcher import OpenCLIPMatcher

TOPICS=[
 ("octopus","octopus","A bright hand-drawn 2D cartoon illustration of a friendly octopus underwater"),
 ("earth","Earth globe","A stylized educational 2D illustration of planet Earth from space"),
 ("volcano","volcano","A simple bold colorful 2D cartoon illustration of a volcano erupting"),
]
root=Path("vector-test")
root.mkdir(exist_ok=True)
model=OpenCLIPMatcher()
out=[]
for key,search,prompt in TOPICS:
    scene={"scene_id":key,"visual_style":"cartoon",
           "visual_query_en":prompt,"search_terms_en":search}
    result=build_scene_asset(scene,root,matcher=model)
    coverage={"topic":key,"matched":bool(result.file),
              "provider":result.source,"reason":result.reason,
              "license":result.license_name,
              "original_url":result.original_url,
              "requires_visual_review":True}
    if result.file:
        with Image.open(result.file) as im:
            rgba=im.convert("RGBA")
            coverage["image_size"]=list(im.size)
            coverage["has_alpha"]=rgba.getchannel("A").getextrema()[0]<255
    out.append(coverage)
    print(json.dumps(coverage,ensure_ascii=False),flush=True)
report={"artistic_approval":"NOT_PERFORMED",
        "coverage":out,"all_three_matched":all(x["matched"] for x in out)}
(root/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
if not report["all_three_matched"]:
    raise SystemExit("Imagens vetoriais adequadas ainda não estão disponíveis para todos os temas")
