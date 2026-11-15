"""Execute editorial and video-integrity checks for an episode.

Usage:
 python -m qa.episode_gate --script roteiro.txt --story storyboard.json --video episodio.mp4
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .editorial_integrity import check_storyboard
from .video_integrity_audit import audit


def inspect(script, storyboard, video=None):
    editorial = check_storyboard(script, storyboard)
    result = {"editorial": editorial, "technical": None,
              "ready_for_artistic_review": False, "approved_for_publication": False}
    if video is not None:
        try:
            result["technical"] = audit(video)
        except (OSError, ValueError, RuntimeError) as exc:
            result["technical"] = {"technical_passed": False, "error": str(exc)}
    result["ready_for_artistic_review"] = (
        editorial["passed"] and
        isinstance(result["technical"], dict) and
        result["technical"].get("technical_passed", False))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--script", required=True, type=Path)
    p.add_argument("--story", required=True, type=Path)
    p.add_argument("--video", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = inspect(args.script.read_text(encoding="utf-8"),
                     json.loads(args.story.read_text(encoding="utf-8")), args.video)
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0 if result["ready_for_artistic_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
