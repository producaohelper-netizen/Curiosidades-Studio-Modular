"""Readable vertical captions for short-form frames; no external services."""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
import textwrap


def caption_frame(frame: Image.Image, text: str, *, max_chars: int = 25) -> Image.Image:
    """Overlay a short caption in the central safe area of a 9:16 frame."""
    if not text or not text.strip():
        return frame
    if frame.width >= frame.height:
        raise ValueError("Reels captions require portrait orientation")
    if len(text) > 160:
        raise ValueError("Caption must be a short spoken phrase")
    result = frame.convert("RGBA").copy()
    draw = ImageDraw.Draw(result, "RGBA")
    font_size = max(18, round(result.width * 0.060))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    lines = textwrap.wrap(text.strip(), width=max_chars, break_long_words=False)
    if len(lines) > 4:
        raise ValueError("Caption exceeds four lines")
    spacing = round(font_size * 0.24)
    boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_height = max(box[3] - box[1] for box in boxes) + spacing
    total_height = len(lines) * line_height
    top = round(result.height * 0.70) - total_height // 2
    pad = round(result.width * 0.035)
    max_width = max(box[2] - box[0] for box in boxes)
    left = (result.width - max_width) // 2
    draw.rounded_rectangle((left-pad, top-pad, left+max_width+pad,
                            top+total_height+pad), radius=round(pad*.6),
                           fill=(9, 18, 31, 205))
    for i, (line, box) in enumerate(zip(lines, boxes)):
        x = (result.width - (box[2]-box[0])) // 2
        y = top + i * line_height
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255),
                  stroke_width=max(1, font_size//22), stroke_fill=(0,0,0,255))
    return result.convert("RGB")
