"""Split long section-level narration captions into readable screen-sized cards.

Card timing is distributed across the measured section duration. This is NOT
word-level forced alignment, and must not be represented as such.
"""
from __future__ import annotations
import math
import textwrap


def caption_cards(text: str, *, max_chars=25, max_lines=3):
    words = text.split()
    if not words:
        return [""]
    cards, current = [], []
    for word in words:
        proposal = " ".join(current + [word])
        lines = textwrap.wrap(proposal, width=max_chars, break_long_words=False)
        if current and (len(lines) > max_lines or len(proposal) > 110):
            cards.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        cards.append(" ".join(current))
    return cards


def caption_at(text: str, elapsed: float, duration: float):
    if not math.isfinite(elapsed) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("Tempo de legenda inválido")
    cards = caption_cards(text)
    index = min(len(cards)-1, max(0, int(elapsed / duration * len(cards))))
    return cards[index]
