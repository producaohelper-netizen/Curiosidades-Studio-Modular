"""Select expressive sprite poses without requiring new image generation.

A pose sheet remains optional. This module does not invent missing art.
"""
from __future__ import annotations
import math
from PIL import Image
from .sprites import SpriteError


def pose_index(elapsed: float, frames: int, fps: float = 8, *,
               loop: bool = True, hold_first: float = 0.0) -> int:
    if not isinstance(frames, int) or isinstance(frames, bool) or frames < 1:
        raise SpriteError("Quantidade de poses invalida")
    if not math.isfinite(float(fps)) or fps <= 0:
        raise SpriteError("Velocidade de poses invalida")
    if not math.isfinite(float(elapsed)) or not math.isfinite(float(hold_first)):
        raise SpriteError("Tempo de pose invalido")
    if hold_first < 0:
        raise SpriteError("Espera inicial invalida")
    tick = int(max(0.0, elapsed - hold_first) * fps)
    return tick % frames if loop else min(frames - 1, tick)


def expressive_frame(sheet: Image.Image, elapsed: float, *,
                     rows: int, columns: int, frames: int,
                     fps: float = 8, loop: bool = True,
                     hold_first: float = 0) -> Image.Image:
    if any(not isinstance(x, int) or isinstance(x, bool) or x < 1
           for x in (rows, columns, frames)):
        raise SpriteError("Grade de poses invalida")
    if frames > rows * columns or sheet.width % columns or sheet.height % rows:
        raise SpriteError("Folha de poses inconsistente")
    index = pose_index(elapsed, frames, fps, loop=loop, hold_first=hold_first)
    w, h = sheet.width // columns, sheet.height // rows
    x, y = index % columns, index // columns
    return sheet.crop((x*w, y*h, (x+1)*w, (y+1)*h))
