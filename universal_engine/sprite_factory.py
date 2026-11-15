"""Sprites consistentes com geração local e recorte automático opcional.

Um asset_id reutiliza o MESMO PNG RGBA em todas as cenas; a fábrica não
regenera o personagem por tomada. Falha se o recorte não tiver transparência
ou ocupar quase todo o quadro (indício de segmentação ruim).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from PIL import Image


class SpriteError(RuntimeError):
    pass


def sprite_filename(asset_id: str):
    if not isinstance(asset_id, str) or not asset_id.strip():
        raise SpriteError("asset_id ausente")
    return hashlib.sha256(asset_id.encode("utf8")).hexdigest()[:24] + ".png"


def assert_cutout(path: str | Path):
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        if image.mode != "RGBA":
            raise SpriteError("Recorte deve ter canal alfa RGBA")
        extrema = rgba.getchannel("A").getextrema()
        if not extrema or extrema[0] >= 240:
            raise SpriteError("Recorte sem transparência útil")
        if extrema[1] <= 30:
            raise SpriteError("Recorte totalmente transparente")
        pixels = rgba.getchannel("A")
        hist = pixels.histogram()
        occupied = sum(hist[128:]) / max(1, rgba.width * rgba.height)
        if not .01 < occupied < .92:
            raise SpriteError(f"Recorte suspeito: {occupied:.1%} de área ocupada")
    return path


def cutout_with_rembg(src: str | Path, dst: str | Path, remover=None):
    """CPU capable, but first real use downloads a local segmentation model."""
    from io import BytesIO
    if remover is None:
        try:
            from rembg import remove
        except ImportError as exc:
            raise SpriteError("Instale rembg[cpu] para recortar os personagens") from exc
        remover = remove
    data = Path(src).read_bytes()
    output = remover(data)
    with Image.open(BytesIO(output)) as image:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGBA").save(dst, "PNG")
    return assert_cutout(dst)


def produce_sprite(actor: dict, root: str | Path, workflow: str | Path | None,
                   *, generator=None, remover=None):
    """Local ComfyUI + rembg, always preserving identity by asset_id."""
    from .local_generator import generate
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    asset_id = actor.get("asset_id")
    target = root / sprite_filename(asset_id)
    manifest = target.with_suffix(".json")
    if target.exists():
        assert_cutout(target)
        return target
    if not workflow:
        raise SpriteError(f"Personagem {asset_id} ausente e workflow de geração não configurado")
    # Style + seed are stable for a given actor across scenes.
    seed = int(hashlib.sha256(asset_id.encode("utf8")).hexdigest()[:8], 16)
    raw = target.with_name(target.stem + "_raw.png")
    name = actor.get("display_name") or actor.get("label") or actor["id"]
    prompt = ("Original clean 2D educational explainer cartoon, isolated full-body "
              f"single subject: {name}, category {actor['kind']}, recognizable "
              "silhouette, consistent bold ink outlines, vibrant flat coloring, "
              "front 3/4 view, neutral pose, entire body visible, plain white "
              "background, no text, no scene, no props, no extra characters")
    render = generator or generate
    try:
        render(prompt, str(workflow), raw, seed=seed)
        cutout_with_rembg(raw, target, remover=remover)
        manifest.write_text(json.dumps({"asset_id":asset_id,"actor":name,
            "seed":seed,"prompt":prompt,"generator":"local-comfyui",
            "segmentation":"rembg","requires_visual_review":True},
            ensure_ascii=False, indent=2),encoding="utf8")
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return target
