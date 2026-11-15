"""Generate THREE different cartoon actors with a REAL local Ollama model.

This test is deliberately NOT part of release approval. It measures whether a
small CPU-friendly language model can produce usable original vector sprites.
"""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from universal_engine.vector_drawer import generate_actor

root=Path("ollama-vector-test")
root.mkdir(exist_ok=True)
actors=[
 {"id":"octopus","asset_id":"octopus","kind":"animal",
  "visual_query_en":"friendly orange octopus with eight curled arms and large expressive eyes"},
 {"id":"earth","asset_id":"earth","kind":"planet",
  "visual_query_en":"planet Earth blue oceans green continents simple cute face and thin outline"},
 {"id":"volcano","asset_id":"volcano","kind":"object",
  "visual_query_en":"cone shaped erupting volcano red lava orange smoke dark rock silhouette"},
]
results=[]
for actor in actors:
    path=root/(actor["id"]+".png")
    try:
        generate_actor(actor,path,model="qwen2.5:1.5b")
        with Image.open(path) as im:
            rgba=im.convert("RGBA")
            extrema=rgba.getchannel("A").getextrema()
            results.append({"actor":actor["id"],"status":"rendered",
                            "size":im.size,"alpha_extrema":extrema,
                            "bytes":path.stat().st_size,
                            "artistic_approval":"NOT_PERFORMED"})
    except Exception as exc:
        results.append({"actor":actor["id"],"status":"failed",
                        "error":type(exc).__name__+": "+str(exc)})
canvas=Image.new("RGB",(3*420,420),(30,47,66))
for i,record in enumerate(results):
    if record["status"]!="rendered":continue
    with Image.open(root/(record["actor"]+".png")) as im:
        sprite=im.convert("RGBA")
        sprite.thumbnail((370,350))
        canvas.paste(sprite,(i*420+(420-sprite.width)//2,45),sprite)
    ImageDraw.Draw(canvas).text((i*420+12,10),record["actor"],fill="white")
canvas.save(root/"contact.jpg",quality=90)
report={"model":"qwen2.5:1.5b","scope":"CPU cartoon vector feasibility",
        "results":results,"artistic_approval":"NOT_PERFORMED",
        "passed_basic_rasterization":all(x["status"]=="rendered" for x in results)}
(root/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
if not report["passed_basic_rasterization"]:
    raise SystemExit("IA local de desenho não gerou todos os personagens")
