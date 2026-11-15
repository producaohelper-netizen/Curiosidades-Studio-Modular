"""Detect exact repeated visual assets without confusing shared characters with errors.

This report is diagnostic, not a substitute for human visual review.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path


def _digest(path):
    file = Path(path)
    if not file.is_file():
        raise FileNotFoundError(file)
    h = sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_scene_backgrounds(entries):
    """entries: (scene_id, background_path) pairs, in episode order."""
    by_hash = defaultdict(list)
    for scene_id, path in entries:
        by_hash[_digest(path)].append(str(scene_id))
    duplicates = [scenes for scenes in by_hash.values() if len(scenes) > 1]
    return {
        "scene_count": len(entries),
        "unique_backgrounds": len(by_hash),
        "repeated_background_groups": duplicates,
        "repeated_scene_count": sum(len(group) for group in duplicates),
        "visual_review_required": bool(duplicates),
        "artistic_approval": "NOT_PERFORMED",
        "note": "Exact background duplicates are flagged for review; intentional settings may repeat."
    }
