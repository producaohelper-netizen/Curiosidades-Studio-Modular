"""Editorial contract for short-form 'Fatos Que Parecem Mentira' episodes.

This module intentionally does not claim fact-checking from LLM output.
No unverified script is authorized for publication.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

PILLARS = {
    "historia_real": 35,
    "ciencia_natureza": 30,
    "misterios_documentados": 20,
    "cotidiano": 15,
}
TARGET_DURATIONS = (25, 45)
BRAND = "Fatos Que Parecem Mentira"


class ShortFormError(ValueError):
    pass


def choose_pillar(counts: dict[str, int]) -> str:
    """Pick the largest deficit against the 30-day editorial mix."""
    if any(k not in PILLARS for k in counts):
        raise ShortFormError("Pilar desconhecido")
    if any(not isinstance(v, int) or v < 0 for v in counts.values()):
        raise ShortFormError("Contagem inválida")
    total = sum(counts.values())
    return max(PILLARS, key=lambda key: ((total + 1) * PILLARS[key] / 100) - counts.get(key, 0))


def validate_reel(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ShortFormError("Roteiro precisa ser um objeto")
    pillar = payload.get("pillar")
    if pillar not in PILLARS:
        raise ShortFormError("Pilar editorial inválido")
    duration = payload.get("target_seconds")
    if duration not in TARGET_DURATIONS:
        raise ShortFormError("Duração alvo deve ser 25 ou 45 segundos")
    sections = payload.get("sections")
    if not isinstance(sections, dict):
        raise ShortFormError("Seções do roteiro ausentes")
    keys = ("hook", "context", "development", "reveal")
    for key in keys:
        if not isinstance(sections.get(key), str) or not sections[key].strip():
            raise ShortFormError("Trecho obrigatório ausente: " + key)
    hook = sections["hook"].strip()
    if len(hook.split()) > 17:
        raise ShortFormError("Gancho longo demais para os primeiros segundos")
    words = len(" ".join(sections[k] for k in keys).split())
    # Wide editorial bounds; actual audio duration must be measured after Piper.
    lower, upper = (35, 85) if duration == 25 else (65, 145)
    if not lower <= words <= upper:
        raise ShortFormError(f"Roteiro de {duration}s com {words} palavras (esperado {lower}–{upper})")
    facts = payload.get("claims")
    if not isinstance(facts, list) or not facts:
        raise ShortFormError("Afirmações e evidências ausentes")
    for claim in facts:
        if not isinstance(claim, dict) or claim.get("status") not in ("verified", "hypothesis", "unknown"):
            raise ShortFormError("Cada afirmação deve distinguir fato, hipótese ou dúvida")
        if not isinstance(claim.get("text"), str) or not claim["text"].strip():
            raise ShortFormError("Afirmação vazia")
    sources = payload.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise ShortFormError("São necessárias duas fontes para revisão")
    for source in sources:
        if not isinstance(source, dict) or not all(
            isinstance(source.get(k), str) and source[k].strip()
            for k in ("title", "url", "publisher")
        ):
            raise ShortFormError("Fonte sem título, endereço ou responsável")
        if not re.match(r"^https?://", source["url"]):
            raise ShortFormError("Fonte deve possuir URL HTTP(S)")
    if len({s["url"].strip().lower() for s in sources}) < 2:
        raise ShortFormError("Fontes duplicadas")
    return {
        "brand": BRAND, "pillar": pillar, "target_seconds": duration,
        "word_count": words, "narration": " ".join(sections[k].strip() for k in keys),
        "sections": sections, "claims": facts, "sources": sources,
        "source_verification": "PENDING_INDEPENDENT_CHECK",
        "publication_approved": False,
        "format": {"width": 1080, "height": 1920, "fps": 24},
        "visual_requirements": {
            "captions": True, "hook_immediately": True,
            "no_intro_logo": True, "original_editing": True,
            "visual_change_interval_seconds": [1, 3]
        },
    }
