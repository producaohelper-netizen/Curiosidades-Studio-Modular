"""Associação texto-imagem com OpenCLIP local e bloqueio de ambiguidade.

A pontuação de similaridade não prova que a imagem explica corretamente a cena.
Usar um prompt visual em inglês validado, não a fala inteira em português.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence
import json, math, os
from .media_sources import MediaCandidate

@dataclass(frozen=True)
class MatchDecision:
    status: str # selected | review_required | no_candidates
    image_url: str | None
    similarity: float | None
    margin: float | None
    title: str | None
    reason: str
    attribution: str | None

class OpenCLIPMatcher:
    """Model is loaded lazily and reused for every scene in an episode."""
    def __init__(self, model_name="ViT-B-32", pretrained="laion2b_s34b_b79k"):
        try:
            import open_clip
            import torch
        except ImportError as e:
            raise RuntimeError("Instale open_clip_torch e torch para associação visual real") from e
        self.torch=torch
        self.model,self.preprocess=open_clip.create_model_and_transforms(
            model_name,pretrained=pretrained,device="cpu"
        )[:2]
        self.model.eval()
        self.tokenizer=open_clip.get_tokenizer(model_name)

    def score(self, visual_prompt_en: str, images: Sequence[Path]) -> list[float]:
        from PIL import Image
        torch=self.torch
        with torch.inference_mode():
            txt=self.tokenizer([visual_prompt_en])
            t=self.model.encode_text(txt)
            t=t / t.norm(dim=-1, keepdim=True)
            vectors=[]
            for image in images:
                with Image.open(image) as im:
                    tensor=self.preprocess(im.convert("RGB")).unsqueeze(0)
                v=self.model.encode_image(tensor)
                v=v/v.norm(dim=-1,keepdim=True)
                vectors.append(v)
            if not vectors: return []
            sims=torch.cat(vectors,dim=0) @ t.T
            return [float(x) for x in sims.flatten().cpu().tolist()]

def decide(candidates: Sequence[MediaCandidate], similarity: Sequence[float],
           *, minimum: float = 0.27, margin_required: float = 0.015) -> MatchDecision:
    """Conservative threshold values are tuneable, NOT validated quality scores."""
    if not candidates:
        return MatchDecision("no_candidates",None,None,None,None,"Sem imagens licenciadas",None)
    if len(candidates)!=len(similarity):
        raise ValueError("Quantidade de candidatos difere de pontuações")
    if any(not math.isfinite(float(s)) for s in similarity):
        raise ValueError("Pontuação CLIP inválida")
    ranked=sorted(range(len(similarity)),key=lambda i:similarity[i],reverse=True)
    top=ranked[0]
    score=float(similarity[top])
    delta=score-float(similarity[ranked[1]]) if len(ranked)>1 else None
    cand=candidates[top]
    clear=score>=minimum and (delta is None or delta>=margin_required)
    reason=("Imagem classificada, verificar coerência factual e licença" if clear
           else "Sem correspondência visual confiável; requer revisão ou geração de asset")
    return MatchDecision("selected" if clear else "review_required",
                         cand.image_url if clear else None,score,delta,
                         cand.title if clear else None,reason,
                         cand.attribution if clear else None)

def match_scene(scene: dict, candidates: Sequence[MediaCandidate], downloaded_images: Sequence[str | Path],
                matcher: OpenCLIPMatcher, minimum:float = .27):
    query=scene.get("visual_query_en", "")
    if not isinstance(query,str) or len(query.strip())<12:
        raise ValueError("Cena exige visual_query_en explícito e descritivo")
    return decide(candidates,matcher.score(query,[Path(p) for p in downloaded_images]),minimum=minimum)

def export_decision(scene_id:str, decision:MatchDecision, path:str|Path):
    file=Path(path);file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps({"scene_id":scene_id,**asdict(decision)},ensure_ascii=False,indent=2),
                    encoding="utf8")
    return file
