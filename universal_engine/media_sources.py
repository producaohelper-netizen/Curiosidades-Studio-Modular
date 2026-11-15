"""Aquisição de imagens com licenças verificáveis.

Fonte inicial: Wikimedia Commons, API MediaWiki oficial. Imagens sem licença
adequada ou metadados suficientes são rejeitadas; nunca presumir domínio público.
Nenhum upload/publicação é efetuado.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from html import unescape
import json, re, hashlib
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "CuriosidadesStudio/0.1 (educational-video-asset-research; contact: local-user)"
ACCEPTABLE_LICENSES = (
    "cc0", "cc-by", "cc by", "cc-by-sa", "cc by-sa",
    "public domain", "pd-old", "pd-us", "pd-art", "pd-self", "pdm",
)
REJECT_MARKERS = ("nc", "nd", "noncommercial", "no derivatives", "fair use", "all rights reserved")
HTML_TAGS = re.compile(r"<[^>]+>")

def clean_html(text: str) -> str:
    return unescape(HTML_TAGS.sub(" ", text or "")).strip()

@dataclass(frozen=True)
class MediaCandidate:
    title: str
    image_url: str
    page_url: str
    license_name: str
    license_url: str
    artist: str
    description: str
    attribution: str
    source: str = "Wikimedia Commons"
    license_verified: bool = True

def _value(meta: dict, key: str) -> str:
    value = meta.get(key, {})
    if isinstance(value, dict): value = value.get("value", "")
    return clean_html(str(value or ""))

def permitted_license(name: str, license_url: str) -> bool:
    label = (name + " " + license_url).casefold()
    if not label.strip() or any(bad in label for bad in REJECT_MARKERS):
        return False
    return any(word in label for word in ACCEPTABLE_LICENSES)

def parse_image(page: dict) -> MediaCandidate | None:
    title = page.get("title", "")
    if not title.startswith("File:"): return None
    infos = page.get("imageinfo") or []
    if not infos: return None
    info = infos[0]
    meta = info.get("extmetadata") or {}
    license_name = _value(meta, "LicenseShortName")
    license_url = _value(meta, "LicenseUrl")
    restriction = _value(meta, "Restrictions")
    if restriction and any(marker in restriction.casefold() for marker in REJECT_MARKERS):
        return None
    if not permitted_license(license_name, license_url): return None
    artist = _value(meta, "Artist")
    attribution = _value(meta, "AttributionRequired")
    page_url = info.get("descriptionurl", "")
    url = info.get("thumburl") or info.get("url", "")
    if not (isinstance(url, str) and url.startswith("https://") and
            isinstance(page_url, str) and page_url.startswith("https://")):
        return None
    description = _value(meta, "ImageDescription")
    line = f"{title}; {artist or 'autor não identificado'}; {license_name}; {license_url}; {page_url}"
    return MediaCandidate(title, url, page_url, license_name, license_url,
                          artist, description, line)

def search_commons(query: str, limit: int = 20, fetch_json=None,
                   filetype: str = 'bitmap') -> list[MediaCandidate]:
    """Searches files by title/description; caller can inject deterministic HTTP fixture."""
    if not isinstance(query, str) or not query.strip(): raise ValueError("query vazia")
    limit = max(1, min(int(limit), 30))
    if filetype not in ("bitmap","drawing"):raise ValueError("filetype inválido")
    params = {
        "action":"query","generator":"search","gsrsearch":query+" filetype:"+filetype,
        "gsrnamespace":"6","gsrlimit":str(limit),"prop":"imageinfo",
        "iiprop":"url|extmetadata","iiurlwidth":"1280","format":"json",
        "formatversion":"2"
    }
    if fetch_json is None:
        def fetch_json(url):
            req=Request(url,headers={"User-Agent":USER_AGENT})
            with urlopen(req, timeout=20) as response:
                return json.load(response)
    payload = fetch_json(API+"?"+urlencode(params))
    candidates = []
    for page in payload.get("query",{}).get("pages",[]):
        item = parse_image(page)
        if item is not None: candidates.append(item)
    return candidates

def save_manifest(candidates: list[MediaCandidate], destination: str | Path):
    dest=Path(destination);dest.parent.mkdir(parents=True,exist_ok=True)
    data={"schema_version":1,"images":[asdict(c) for c in candidates],
          "needs_individual_license_review":True,
          "note":"Verificar autoria, contexto e outras restrições antes da publicação."}
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    return dest

def cache_key(item: MediaCandidate) -> str:
    return hashlib.sha256(item.image_url.encode("utf8")).hexdigest()[:24]
