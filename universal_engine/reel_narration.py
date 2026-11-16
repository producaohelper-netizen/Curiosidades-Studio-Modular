"""Synthesize short-form narration in phrases with Piper and build timed captions.

This is a narration stage, not a complete video generator. Source verification
and artistic approval remain required before publishing.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .shortform import validate_reel
from .narration import generate_piper
from .reel_phrase_audio import join_phrase_wavs


def synthesize_reel(payload, model, output_dir, *, piper="piper", synth=generate_piper):
    plan = validate_reel(payload)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    sections = plan["sections"]
    phrases = []
    for i, key in enumerate(("hook", "context", "development", "reveal"), start=1):
        text = sections[key].strip()
        target = root / f"phrase_{i:02d}.wav"
        result = synth(text, model, target, executable=piper)
        if not target.is_file():
            raise RuntimeError(f"Piper não criou o trecho {key}")
        phrases.append((text, target))
    timing = join_phrase_wavs(phrases, root / "narracao_reel.wav")
    if not 20 <= timing["duration"] <= 60:
        raise ValueError(f"Narração com {timing['duration']:.1f}s; exige 20 a 60s")
    result = {
        "format": plan["format"],
        "brand": plan["brand"],
        "target_seconds": plan["target_seconds"],
        "audio_seconds": timing["duration"],
        "audio_path": str(root / "narracao_reel.wav"),
        "reel_caption_cues": timing["cues"],
        "source_verification": "PENDING_INDEPENDENT_CHECK",
        "publication_approved": False,
    }
    (root / "narracao_e_legendas.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8"
    )
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="JSON do roteiro curto")
    ap.add_argument("--voice-model", required=True)
    ap.add_argument("--piper", default="piper")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf8"))
        result = synthesize_reel(data, args.voice_model, args.output_dir, piper=args.piper)
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        ap.exit(2, "Narração curta interrompida: " + str(exc) + "\n")
    print(f"Narração e legendas prontas ({result['audio_seconds']:.1f}s); revisão obrigatória.")


if __name__ == "__main__":
    main()
