"""Build a default ComfyUI API workflow from an already installed checkpoint.

Does not download an unknown or unlicensed checkpoint. Works with standard
CheckpointLoaderSimple/CLIPTextEncode/KSampler/VAEDecode/SaveImage nodes.
Some custom checkpoints may require a specialised workflow and will fail safely.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request, urlopen


class ComfySetupError(RuntimeError):
    pass


def checkpoints(fetch=None):
    if fetch is None:
        def fetch(url):
            with urlopen(Request(url,headers={"User-Agent":"CuriosidadesStudio/1.0"}),
                         timeout=8) as response:
                return json.load(response)
    models = fetch("http://127.0.0.1:8188/models/checkpoints")
    if not isinstance(models,list):
        raise ComfySetupError("ComfyUI retornou lista de checkpoints inválida")
    models=[m for m in models if isinstance(m,str) and m.lower().endswith((".safetensors",".ckpt"))]
    if not models:
        raise ComfySetupError("ComfyUI não possui checkpoint de geração instalado")
    # Prefer general illustrative checkpoints; do not pick a workflow-only model.
    models.sort(key=lambda x:(
        not any(k in x.lower() for k in ("toon","cartoon","illustrat","dreamshaper")),
        x.casefold()
    ))
    return models


def make_workflow(checkpoint,*,width=768,height=512,steps=18):
    if not isinstance(checkpoint,str) or not checkpoint.endswith((".safetensors",".ckpt")):
        raise ComfySetupError("Checkpoint inválido")
    if width%8 or height%8:raise ComfySetupError("Dimensões devem ser múltiplas de 8")
    return {
        "3":{"class_type":"KSampler","inputs":{
             "seed":"{{SEED}}","steps":steps,"cfg":6.5,
             "sampler_name":"euler","scheduler":"normal","denoise":1.0,
             "model":["4",0],"positive":["6",0],"negative":["7",0],
             "latent_image":["5",0]}},
        "4":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":checkpoint}},
        "5":{"class_type":"EmptyLatentImage","inputs":{
             "width":width,"height":height,"batch_size":1}},
        "6":{"class_type":"CLIPTextEncode","inputs":{
             "text":"{{PROMPT}}","clip":["4",1]}},
        "7":{"class_type":"CLIPTextEncode","inputs":{
             "text":"watermark, signature, duplicate subjects, malformed hands, text, logo, blurry",
             "clip":["4",1]}},
        "8":{"class_type":"VAEDecode","inputs":{
             "samples":["3",0],"vae":["4",2]}},
        "9":{"class_type":"SaveImage","inputs":{
             "filename_prefix":"CuriosidadesStudio","images":["8",0]}}
    }


def auto_workflow(path,*,fetch=None):
    available=checkpoints(fetch=fetch)
    chosen=available[0]
    sdxl="xl" in chosen.lower()
    graph=make_workflow(chosen,width=1024 if sdxl else 768,
                        height=576 if sdxl else 512)
    dst=Path(path);dst.parent.mkdir(parents=True,exist_ok=True)
    # Ensure template markers stay as JSON strings for local_generator.
    dst.write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding="utf8")
    return {"workflow":str(dst),"checkpoint":chosen,
            "requires_model_license_review":True,"engine":"ComfyUI local"}
