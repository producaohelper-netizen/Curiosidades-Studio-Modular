"""Validate that the isolated foreground is relevant to its intended actor.

A scene-wide photo match is insufficient: segmentation may select the wrong
foreground object. Similarity is a conservative heuristic, not proof of truth.
"""
from pathlib import Path


class ForegroundMismatch(RuntimeError):
    pass


def verify_foreground(actor: dict, scene: dict, sprite_path: str | Path,
                      *, matcher=None, minimum=.23):
    from .visual_pipeline import _shared_matcher
    phrase=(actor.get("visual_query_en") or actor.get("label_en") or
            scene.get("search_terms_en") or scene.get("visual_query_en"))
    if not isinstance(phrase,str) or len(phrase.strip())<5:
        raise ForegroundMismatch("Sem descrição em inglês do sujeito extraído")
    ranker=matcher or _shared_matcher()
    scores=ranker.score("isolated photo of "+phrase,[Path(sprite_path)])
    if not scores:
        raise ForegroundMismatch("OpenCLIP não retornou pontuação do recorte")
    score=float(scores[0])
    if score<minimum:
        raise ForegroundMismatch(
            f"Recorte não parece corresponder a '{phrase}': score {score:.3f} "
            f"abaixo de {minimum:.3f}; gere ou escolha outra imagem"
        )
    return {"subject_text":phrase,"score":score,
            "requires_visual_review":True,
            "note":"Similaridade por IA não garante precisão factual"}
