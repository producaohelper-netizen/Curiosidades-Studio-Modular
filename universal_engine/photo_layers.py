"""Alternative scene layers for CPU-only computers using licensed photos.

Only supports scenes with one foreground actor. A dominant subject is segmented
with rembg; the hole left behind is filled, then artistically filtered.
This is NOT equivalent to professional animation: report requires review.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from io import BytesIO

from .sprite_factory import assert_cutout, SpriteError


class LayerExtractionError(RuntimeError):
    pass


def photo_layers(image_path: str | Path, background_out: str | Path,
                 foreground_out: str | Path, *,
                 remover=None, background_filler=None):
    from .sprite_factory import cutout_with_rembg
    source = Path(image_path)
    background_out = Path(background_out)
    foreground_out = Path(foreground_out)
    background_out.parent.mkdir(parents=True, exist_ok=True)
    foreground_out.parent.mkdir(parents=True, exist_ok=True)
    try:
        cutout_with_rembg(source,foreground_out,remover=remover)
    except (SpriteError, OSError, ValueError) as exc:
        raise LayerExtractionError("Não foi possível isolar sujeito da fotografia") from exc

    with Image.open(source) as im:
        original=im.convert("RGB")
    with Image.open(foreground_out) as im:
        alpha=im.getchannel("A")
    mask=alpha.resize(original.size,Image.Resampling.LANCZOS)
    if background_filler is not None:
        bg=background_filler(original,mask)
    else:
        # Telea inpainting is effective for small regions; large subjects need
        # editorial review and a generated background instead.
        try:
            import cv2
            import numpy as np
            arr=np.asarray(original)
            m=np.asarray(mask).copy()
            m=(m>70).astype("uint8")*255
            filled=cv2.inpaint(cv2.cvtColor(arr,cv2.COLOR_RGB2BGR),
                               m,5,cv2.INPAINT_TELEA)
            bg=Image.fromarray(cv2.cvtColor(filled,cv2.COLOR_BGR2RGB))
        except ImportError:
            bg=original.filter(ImageFilter.GaussianBlur(radius=28))
    if not isinstance(bg,Image.Image):
        raise LayerExtractionError("O preenchimento não devolveu imagem válida")
    # Mild colour grading to reduce photographic / cartoon style collision.
    bg=ImageEnhance.Color(bg.convert("RGB")).enhance(.87)
    bg=ImageEnhance.Contrast(bg).enhance(1.08)
    bg.save(background_out,"PNG")
    assert_cutout(foreground_out)
    return {"background":str(background_out),"sprite":str(foreground_out),
            "source":"licensed-photo-foreground",
            "review_required":True,
            "warning":"Contornos, identidade do sujeito e preenchimento de fundo exigem revisão"}


def extract_for_scene(scene, image_path, sprite_path, background_path, *,
                      remover=None, background_filler=None):
    actors=scene.get("actors",[])
    if len(actors)!=1:
        raise LayerExtractionError("Extração de foto suporta apenas 1 ator; "
                                   "use gerador local para cenas com vários atores")
    return photo_layers(image_path,background_path,sprite_path,
                        remover=remover,background_filler=background_filler)
