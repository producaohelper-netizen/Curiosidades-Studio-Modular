"""Render a Reel using a JSON manifest with multiple approved images per section.

Manifest example:
{"narration_json":"output/narracao_e_legendas.json",
 "images":[["hook1.png","hook2.png"],["context.png"],
           ["detail1.png","detail2.png"],["reveal.png"]]}
Relative paths are resolved against the manifest directory.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .reel_render import render_reel
from .reel_visual_sequence import normalize_images


def render_manifest(path, output, *, ffmpeg="ffmpeg"):
    source = Path(path).resolve()
    data = json.loads(source.read_text(encoding="utf8"))
    narration_path = (source.parent / data["narration_json"]).resolve()
    narration = json.loads(narration_path.read_text(encoding="utf8"))
    sections = normalize_images(data["images"], len(narration["reel_caption_cues"]))
    images = [[(source.parent / item).resolve() for item in section] for section in sections]
    audio = Path(narration["audio_path"])
    if not audio.is_absolute():
        audio = (narration_path.parent / audio).resolve()
    result = render_reel(audio, narration["reel_caption_cues"], images, output, ffmpeg=ffmpeg)
    Path(output).with_suffix(".review.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    try:
        render_manifest(args.manifest, args.output, ffmpeg=args.ffmpeg)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(2, "Falha no manifesto visual: " + str(exc) + "\n")
    print("Reel com múltiplas imagens criado para revisão.")


if __name__ == "__main__":
    main()
