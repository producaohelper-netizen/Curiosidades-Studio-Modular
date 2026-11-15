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
import json, hashlib, time, re
from functools import lru_cache
from .media_sources import search_commons, MediaCandidate
from .visual_matcher import OpenCLIPMatcher, match_scene
from .local_generator import generate, GenerationError
from .style_matcher import cartoon_indices, actor_indices

class AssetPipelineError(RuntimeError):
    pass

@lru_cache(maxsize=1)
def _shared_matcher():
    # Reuse expensive CPU OpenCLIP weights across all 40-100 scenes.
    return OpenCLIPMatcher()

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
    visual_style: str = ""

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
        # Keep alpha on SVG raster thumbnails and illustrated PNGs. A
        # transparent drawing is a real reusable layer, not a photograph
        # that needs destructive AI masking and inpainting.
        rgba=im.convert("RGBA")
        alpha=rgba.getchannel("A").getextrema()
        image=rgba if alpha[0]<255 else im.convert("RGB")
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
    # Retomar renderizações interrompidas sem baixar as mesmas imagens.
    manifest=work/"asset.json"
    if manifest.exists():
        try:
            cached=SceneAsset(**json.loads(manifest.read_text(encoding="utf8")))
            file=Path(cached.file).resolve() if cached.file else None
            if (cached.scene_id==scene_id and cached.prompt==prompt and
                file is not None and file.is_file() and
                file.is_relative_to(work.resolve()) and file.stat().st_size>1024 and
                cached.visual_style==scene.get('visual_style','')):
                return cached
        except (ValueError,TypeError,OSError,KeyError):
            pass
    lookup=query or scene.get("search_terms_en") or prompt
    if scene.get("visual_style")=="cartoon":
        lookup=str(lookup)+" cartoon illustration drawing"
    search=commons_search or search_commons
    download=downloader or download_commons
    candidates=[];images=[];errors=[]
    try:
        if commons_search is None and scene.get("visual_style")=="cartoon":
            # Vector illustrations are more suitable than photographic cutouts.
            # Wikimedia serves safe raster thumbnails of SVG illustrations.
            found=search(str(scene.get("search_terms_en") or prompt),
                         limit=12,filetype="drawing")
            if len(found)<5:
                found+=search(lookup,limit=12,filetype="bitmap")
        else:
            found=search(lookup,limit=15)
        if scene.get("asset_purpose")=="actor":
            # A labelled anatomy diagram can score highly for "shark"
            # while looking absurd as an animated character.
            diagram_terms=re.compile(
                r"\b(anatomy|anatomical|diagram|labelled|labeled|"
                r"dissection|skeleton|cross[- ]section|schematic|"
                r"bones|organ systems)\b",re.IGNORECASE)
            found=[item for item in found
                   if not diagram_terms.search(item.title+" "+item.description)]
        seen=set()
        unique=[]
        for item in found:
            if item.image_url not in seen:
                seen.add(item.image_url)
                unique.append(item)
        for i,record in enumerate(unique[:24]):
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
            ranker=matcher or _shared_matcher()
            indices=list(range(len(candidates)))
            if scene.get("visual_style")=="cartoon":
                indices=cartoon_indices(ranker,images)
                if not indices:
                    errors.append("Fotos realistas não atendem ao estilo de animação 2D")
            if indices and scene.get("asset_purpose")=="actor":
                suitable=actor_indices(ranker,[images[i] for i in indices])
                indices=[indices[i] for i in suitable]
                if not indices:
                    errors.append(
                        "Desenhos com anotações/anatomia não servem como atores de animação")
            decision=match_scene(scene,[candidates[i] for i in indices],
                                 [images[i] for i in indices],ranker) if indices else None
            if decision is not None and decision.status=="selected":
                index=next(i for i,c in enumerate(candidates) if c.image_url==decision.image_url)
                c=candidates[index]
                final=work/"final.png"
                with Image.open(images[index]) as img:img.save(final)
                result=SceneAsset(scene_id,str(final),"Wikimedia Commons",c.attribution,
                                  True,"Revisão factual e atribuição ainda obrigatórias",prompt,
                                  c.license_name,c.license_url,c.page_url,
                                  scene.get('visual_style',''))
                return _save(result,work)
            if decision is not None:
                errors.append(f'{decision.reason}; similaridade={decision.similarity}; margem={decision.margin}')
        except Exception as exc:
            errors.append(f"OpenCLIP: {type(exc).__name__}")
    if comfy_workflow:
        try:
            generate_image=generator or generate
            image_prompt=(
                'Original 2D cartoon illustration, clean bold ink outlines, flat bright colors, '
                'readable composition, unified art direction, NOT a photograph. '+prompt
                if scene.get('visual_style')=='cartoon' else prompt
            )
            g=generate_image(image_prompt,comfy_workflow,work/"final.png")
            result=SceneAsset(scene_id,g.file,"local-comfyui","",True,
                              "Ilustração de IA exige revisão científica e de consistência",prompt,
                              "CHECK_MODEL_LICENSE","", "",
                              scene.get("visual_style",""))
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
