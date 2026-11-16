"""Deterministic 2-second visual reframing for user-supplied Reel images.

A visual change is a crop/zoom variation, not a claim of a new image or
new factual evidence. Captions are drawn after the reframing.
"""
from __future__ import annotations
import math
from PIL import Image


def reframe(image: Image.Image, seconds_into_section: float, *,
            interval: float = 2.0) -> Image.Image:
    if not math.isfinite(seconds_into_section) or seconds_into_section < 0:
        raise ValueError("Tempo visual inválido")
    if not 1 <= interval <= 3:
        raise ValueError("Intervalo visual deve ser de 1 a 3 segundos")
    if image.width <= 0 or image.height <= 0:
        raise ValueError("Imagem inválida")
    beat = int(seconds_into_section / interval)
    # Every beat changes crop and position, but the approved source remains.
    zoom = (1.0, 1.07, 1.12, 1.04)[beat % 4]
    if zoom == 1.0:
        return image.copy()
    width, height = image.size
    crop_w = max(1, round(width / zoom))
    crop_h = max(1, round(height / zoom))
    fractions = ((.5, .5), (.25, .30), (.75, .65), (.45, .80))
    fx, fy = fractions[beat % len(fractions)]
    left = max(0, min(width - crop_w, round((width - crop_w) * fx)))
    top = max(0, min(height - crop_h, round((height - crop_h) * fy)))
    return image.crop((left, top, left + crop_w, top + crop_h)).resize(
        (width, height), Image.Resampling.BICUBIC)
