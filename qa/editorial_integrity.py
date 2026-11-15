"""Editorial integrity checks before spending hours rendering an episode.

This gate does not claim to verify scientific truth or artistic quality.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict


def normalize(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def check_storyboard(script, storyboard):
    errors = []
    scenes = storyboard.get("scenes") if isinstance(storyboard, dict) else None
    if not isinstance(scenes, list) or not scenes:
        return {"passed": False, "errors": ["Nenhuma cena disponível"]}
    original = normalize(script)
    rebuilt = normalize(" ".join(str(s.get("narration", "")) for s in scenes if isinstance(s, dict)))
    if not original or rebuilt != original:
        errors.append("Roteiro e falas das cenas divergem: há texto alterado, ausente ou fora de ordem")
    identifiers = []
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            errors.append(f"Cena {index + 1}: formato inválido")
            continue
        ident = scene.get("scene_id")
        if not isinstance(ident, str) or not ident.strip():
            errors.append(f"Cena {index + 1}: identificador ausente")
        identifiers.append(ident)
        if not isinstance(scene.get("visual_fact"), str) or not scene["visual_fact"].strip():
            errors.append(f"Cena {index + 1}: fato visual não definido")
        if not isinstance(scene.get("visual_query_en"), str) or len(scene["visual_query_en"].strip()) < 12:
            errors.append(f"Cena {index + 1}: descrição visual insuficiente")
        callout = scene.get("callout", "")
        if callout:
            if not isinstance(callout, str):
                errors.append(f"Cena {index + 1}: legenda inválida")
            else:
                words = lambda t: set(re.findall(r"\w+", t.casefold(), flags=re.UNICODE))
                if not words(callout).issubset(words(str(scene.get("narration", "")))):
                    errors.append(f"Cena {index + 1}: legenda não aparece na narração")
        if not isinstance(scene.get("timeline"), list) or not scene["timeline"]:
            errors.append(f"Cena {index + 1}: sem ações visuais")
    if len(identifiers) != len(set(identifiers)):
        errors.append("Há identificadores de cena duplicados")
    return {"passed": not errors, "errors": errors, "scenes": len(scenes),
            "requires_fact_check": True, "artistic_approval": "PENDING"}
