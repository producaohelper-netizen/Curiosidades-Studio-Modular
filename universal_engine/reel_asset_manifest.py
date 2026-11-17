"""Review-only rights manifest for the four visuals of a Reel.

A license label is a declaration, NOT a verified permission. The reviewer
must inspect the original source, license version and attribution before use.
"""
from __future__ import annotations

import ipaddress
import json
import re
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
        if not isinstance(license_id, str) or license_id not in ALLOWED_LICENSES:
            raise AssetRightsError("Licença não suportada ou ausente")
        if not isinstance(author, str) or not author.strip():
            raise AssetRightsError("Autoria obrigatória")
        if not isinstance(source, str) or not source.strip():
            raise AssetRightsError("Origem da imagem obrigatória")
        if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in source):
            raise AssetRightsError("URL de origem contém espaços ou caracteres de controle")
        try:
            parsed = urlsplit(source)
            hostname = parsed.hostname
            port = parsed.port
        except ValueError as exc:
            raise AssetRightsError("URL de origem malformada") from exc
        if (parsed.scheme != "https" or not hostname or parsed.username or parsed.password
                or port not in (None, 443) or parsed.fragment):
            raise AssetRightsError("Origem deve ser uma URL HTTPS pública sem credenciais")
        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            pass
        else:
            raise AssetRightsError("Endereço IP não é uma fonte pública de direitos verificável")
        if (hostname == "localhost" or "." not in hostname
                or len(hostname) > 253
                or any(not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
                       for label in hostname.split("."))):
            raise AssetRightsError("Domínio de origem inválido")
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
