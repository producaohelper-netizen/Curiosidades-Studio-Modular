"""Timed captions for vertical Reels, using explicit audio-aligned timestamps.

The caller must supply actual alignment timestamps; this module never invents
word-level synchronization from estimated speaking speed.
"""
from __future__ import annotations
import math


class CaptionTimingError(ValueError):
    pass


def validate_cues(cues, duration: float):
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise CaptionTimingError("Duração do áudio inválida")
    if not isinstance(cues, list) or not cues:
        raise CaptionTimingError("Legendas sincronizadas ausentes")
    previous_end = 0.0
    for index, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise CaptionTimingError(f"Legenda {index} inválida")
        start, end, text = cue.get("start"), cue.get("end"), cue.get("text")
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (start, end)):
            raise CaptionTimingError(f"Legenda {index} sem tempos válidos")
        if start < previous_end - 1e-6 or end <= start or end > duration + 0.05:
            raise CaptionTimingError(f"Legenda {index} sobreposta ou fora do áudio")
        if not isinstance(text, str) or not text.strip() or len(text) > 160:
            raise CaptionTimingError(f"Legenda {index} sem texto válido")
        previous_end = end
    return cues


def active_caption(cues, time_sec: float) -> str:
    """Return the caption whose half-open [start, end) interval contains time."""
    for cue in cues:
        if cue["start"] <= time_sec < cue["end"]:
            return cue["text"]
    return ""
