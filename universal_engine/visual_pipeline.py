"""One visual-scene asset pipeline: Commons -> OpenCLIP -> local ComfyUI.

Licenses and scene consistency are reviewed, not guessed. No random filler images.
Requires Internet for Commons, downloaded OpenCLIP weights, and a running ComfyUI
for local generation. An actual demo must independently validate all providers.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from PIL import Image
from io import BytesIO
import json, hashlib, time
from .media_sources import search_commons, MediaCandidate
from .visual_matcher import OpenCLIPMatcher, match_scene
from .local_generator import generate, GenerationError

class AssetPipelineError(RuntimeError):
    pass

@dataclass
class SceneAsset:
    scene_id: str
    file: str | None
    source: str
    attribution: str
    review_required: bool
    reason: str
    prompt: str
    license_name: str
    license_url: str
    original_url: str

def download_commons(item: MediaCandidate, destination: str|Path):
    """Download only Wikimedia-hosted images; decode and re-encode safely."""
    url=urlparse(item.image_url)
    hostname=(url.hostname or "").lower()
    if (url.scheme!="https" or
        not (hostname=="upload.wikimedia.org" or hostname.endswith(".wikimedia.org"))):
        raise AssetPipelineError("Origem de imagem não permitida")
    req=Request(item.image_url,headers={"User-Agent":"CuriosidadesStudio/0.1"})
    with urlopen(req,timeout=25) as response:
        data=response.read(12*1024*1024+1)
    if len(data)>12*1024*1024:
        raise AssetPipelineError("Imagem excede 12 MiB")
    with Image.open(BytesIO(data)) as im:
        if im.width*im.height>28_000_000:
            raise AssetPipelineError("Imagem excede limite de pixels")
        image=im.convert("RGB")
        image.thumbnail((1920,1080))
        dst=Path(destination)
        dst.parent.mkdir(parents=True,exist_ok=True)
        image.save(dst,format="PNG")
    return dst

def build_scene_asset(scene:dict, workspace: str|Path, *,
                      query: str|None=None,
                      matcher=None,
                      commons_search=None,
                      downloader=None,
                      generator=None,
                      comfy_workflow: str|None=None) -> SceneAsset:
    """Produces an asset record. Generated images always require editorial review."""
    scene_id=scene.get("scene_id")
    prompt=scene.get("visual_query_en") or ""
    if not scene_id or not isinstance(prompt,str) or len(prompt)<12:
        raise AssetPipelineError("SceneSpec exige scene_id e visual_query_en")
    root=Path(workspace);root.mkdir(parents=True,exist_ok=True)
    work=root/scene_id
    work.mkdir(parents=True,exist_ok=True)
    lookup=query or prompt
    search=commons_search or search_commons
    download=downloader or download_commons
    candidates=[];images=[];errors=[]
    try:
        for i,record in enumerate(search(lookup,limit=15)):
            try:
                path=download(record,work/f"candidate_{i:02}.png")
                candidates.append(record)
                images.append(path)
            except Exception as exc:
                errors.append(f"Download {i}: {type(exc).__name__}")
    except Exception as exc:
        errors.append(f"Commons: {type(exc).__name__}")
    if candidates:
        try:
            ranker=matcher or OpenCLIPMatcher()
            decision=match_scene(scene,candidates,images,ranker)
            if decision.status=="selected":
                index=next(i for i,c in enumerate(candidates) if c.image_url==decision.image_url)
                c=candidates[index]
                final=work/"final.png"
                with Image.open(images[index]) as img:img.save(final)
                result=SceneAsset(scene_id,str(final),"Wikimedia Commons",c.attribution,
                                  True,"Revisão factual e atribuição ainda obrigatórias",prompt,
                                  c.license_name,c.license_url,c.page_url)
                return _save(result,work)
            errors.append(decision.reason)
        except Exception as exc:
            errors.append(f"OpenCLIP: {type(exc).__name__}")
    if comfy_workflow:
        try:
            generate_image=generator or generate
            g=generate_image(prompt,comfy_workflow,work/"final.png")
            result=SceneAsset(scene_id,g.file,"local-comfyui","",True,
                              "Ilustração de IA exige revisão científica e de consistência",prompt,
                              "CHECK_MODEL_LICENSE","", "")
            return _save(result,work)
        except Exception as exc:
            errors.append(f"ComfyUI: {type(exc).__name__}")
    result=SceneAsset(scene_id,None,"unavailable","",True,
                      "; ".join(errors) or "Nenhuma imagem adequada",prompt,"","","")
    return _save(result,work)

def _save(record:SceneAsset,work:Path):
    (work/"asset.json").write_text(json.dumps(asdict(record),ensure_ascii=False,indent=2),
                                   encoding="utf8")
    return record
