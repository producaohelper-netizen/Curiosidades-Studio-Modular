"""Review-only rights manifest for the four visuals of a Reel.

A license label is a declaration, NOT a verified permission. The reviewer
must inspect the original source, license version and attribution before use.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED_LICENSES = {"CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "PUBLIC-DOMAIN", "OWN-WORK"}


class AssetRightsError(ValueError):
    pass


def validate_asset_manifest(manifest: dict, image_paths: list[str]) -> dict:
    """Match each image to a traceable rights declaration; never approve publication."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get("assets"), list):
        raise AssetRightsError("Manifesto deve conter uma lista assets")
    assets = manifest["assets"]
    if len(assets) != len(image_paths):
        raise AssetRightsError("Cada imagem precisa de um registro de direitos")
    expected = [Path(p).name for p in image_paths]
    actual = []
    for asset in assets:
        if not isinstance(asset, dict):
            raise AssetRightsError("Registro de imagem inválido")
        filename = asset.get("filename")
        license_id = asset.get("license")
        author = asset.get("author")
        source = asset.get("source_url")
        if not isinstance(filename, str) or not filename or Path(filename).name != filename:
            raise AssetRightsError("Nome de imagem inválido")
        if license_id not in ALLOWED_LICENSES:
            raise AssetRightsError("Licença não suportada ou ausente")
        if not isinstance(author, str) or not author.strip():
            raise AssetRightsError("Autoria obrigatória")
        if not isinstance(source, str) or not source.strip():
            raise AssetRightsError("Origem da imagem obrigatória")
        parsed = urlsplit(source)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise AssetRightsError("Origem deve ser uma URL HTTPS pública sem credenciais")
        actual.append(filename)
    if len(set(actual)) != len(actual) or actual != expected:
        raise AssetRightsError("Imagens e manifesto não correspondem na mesma ordem")
    return {
        "assets_documented": len(assets),
        "rights_declarations_present": True,
        "rights_independently_verified": False,
        "publication_approved": False,
        "review_required": "Confirmar autoria, licença, versão, atribuição e pertinência visual",
    }


def load_asset_manifest(path: str, image_paths: list[str]) -> dict:
    return validate_asset_manifest(json.loads(Path(path).read_text(encoding="utf-8")), image_paths)
