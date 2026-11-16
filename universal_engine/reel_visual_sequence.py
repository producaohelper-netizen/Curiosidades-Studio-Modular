"""Choose approved images for each narration section on two-second beats.

A section can have one image (crop/zoom only) or several (actual image cuts).
No unverified or unrelated visual is fetched automatically.
"""
from __future__ import annotations
import math


def normalize_images(images, section_count: int):
    if not isinstance(images, (list, tuple)) or len(images) != section_count:
        raise ValueError("É necessário informar imagens para cada trecho")
    result = []
    for index, item in enumerate(images):
        paths = item if isinstance(item, (list, tuple)) else [item]
        if not paths or not all(isinstance(p, (str, __import__("os").PathLike)) and str(p)
                                for p in paths):
            raise ValueError(f"Imagens inválidas no trecho {index + 1}")
        result.append(list(paths))
    return result


def image_index(seconds_into_section: float, count: int, interval: float = 2.0):
    if not isinstance(count, int) or count < 1:
        raise ValueError("Trecho sem imagens")
    if not math.isfinite(seconds_into_section) or seconds_into_section < 0:
        raise ValueError("Tempo inválido")
    if not 1 <= interval <= 3:
        raise ValueError("Intervalo fora da faixa editorial")
    return int(seconds_into_section / interval) % count
