"""Editorial contract for short-form 'Fatos Que Parecem Mentira' episodes.

This module intentionally does not claim fact-checking from LLM output.
No unverified script is authorized for publication.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from urllib.parse import urlsplit
import ipaddress

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


def _site_identity(host: str) -> str:
    """Conservative registrable-site key for common Brazilian/UK public suffixes.

    This is not a complete public suffix database; manual verification is still
    required for less common suffixes and independently operated subdomains.
    """
    labels = host.lower().strip(".").split(".")
    multi_suffixes = {
        "com.br", "org.br", "gov.br", "edu.br", "net.br",
        "com.uk", "co.uk", "org.uk", "ac.uk", "gov.uk",
        "com.au", "net.au", "org.au", "co.jp", "com.mx",
    }
    suffix = ".".join(labels[-2:])
    count = 3 if suffix in multi_suffixes else 2
    return ".".join(labels[-count:]) if len(labels) >= count else host


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
        if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in source["url"]):
            raise ShortFormError("URL de fonte contém espaços ou caracteres de controle")
        if not re.match(r"^https?://", source["url"]):
            raise ShortFormError("Fonte deve possuir URL HTTP(S)")
    if len({s["url"].strip().lower() for s in sources}) < 2:
        raise ShortFormError("Fontes duplicadas")
    # Two URLs from the same publisher or host are not independent evidence.
    # This is only a structural check: factual verification remains manual.
    publishers = {source["publisher"].strip().casefold() for source in sources}
    hosts = set()
    sites = set()
    for source in sources:
        try:
            parsed = urlsplit(source["url"].strip())
            hostname = parsed.hostname
        except ValueError as exc:
            raise ShortFormError("URL de fonte inválida") from exc
        if parsed.scheme not in ("http", "https") or not hostname:
            raise ShortFormError("URL de fonte inválida")
        if parsed.username is not None or parsed.password is not None:
            raise ShortFormError("URL de fonte não pode conter credenciais")
        try:
            parsed.port
        except ValueError as exc:
            raise ShortFormError("Porta inválida na URL de fonte") from exc
        host = hostname.lower().rstrip(".").removeprefix("www.")
        if any(not label for label in host.split(".")) or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in host.split(".")
        ):
            raise ShortFormError("Domínio de fonte inválido")
        if host == "localhost" or host.endswith(".localhost") or "." not in host:
            raise ShortFormError("Fonte precisa usar domínio público")
        try:
            ipaddress.ip_address(host.strip("[]"))
        except ValueError:
            pass
        else:
            raise ShortFormError("Fonte precisa usar domínio público, não endereço IP")
        hosts.add(host)
        sites.add(_site_identity(host))
    # A subdomain is not independent of its parent site (e.g. news.example.org
    # and example.org). This is conservative; manual publisher checks still apply.
    if any(a == b or a.endswith("." + b) or b.endswith("." + a)
           for index, a in enumerate(hosts) for b in list(hosts)[index + 1:]):
        raise ShortFormError("Use pelo menos duas fontes de sites diferentes")
    if len(publishers) < 2 or len(sites) < 2:
        raise ShortFormError("Use pelo menos duas fontes de responsáveis e sites diferentes")
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
