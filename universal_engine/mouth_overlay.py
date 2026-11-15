"""Overlay a licensed three-pose mouth sprite sheet onto an existing actor.

Mouth positions are authored normalized coordinates on the actor image.
The three cells are closed, small-open, wide-open, in that order.
"""
from __future__ import annotations
import math
from PIL import Image
from .mouth_sync import mouth_pose_at


class MouthOverlayError(ValueError):
    pass


def compose_mouth(actor_image, mouth_sheet, envelope, at, *, x, y, width):
    if not isinstance(actor_image, Image.Image) or not isinstance(mouth_sheet, Image.Image):
        raise MouthOverlayError("Imagens do ator e da boca obrigatorias")
    if any(not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in (x, y, width)):
        raise MouthOverlayError("Coordenadas invalidas")
    if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < width <= 1):
        raise MouthOverlayError("Posicao da boca fora do ator")
    if mouth_sheet.width % 3 or mouth_sheet.width < 3:
        raise MouthOverlayError("Folha de boca exige tres quadros iguais")
    cell_width = mouth_sheet.width // 3
    index = mouth_pose_at(envelope, at)
    mouth = mouth_sheet.convert("RGBA").crop(
        (index * cell_width, 0, (index + 1) * cell_width, mouth_sheet.height))
    base = actor_image.convert("RGBA").copy()
    out_width = max(1, round(base.width * width))
    out_height = max(1, round(mouth.height * out_width / mouth.width))
    mouth = mouth.resize((out_width, out_height), Image.Resampling.LANCZOS)
    left = round(base.width * x - out_width / 2)
    top = round(base.height * y - out_height / 2)
    if left < 0 or top < 0 or left + out_width > base.width or top + out_height > base.height:
        raise MouthOverlayError("Boca ultrapassa os limites do ator")
    base.alpha_composite(mouth, (left, top))
    return base
