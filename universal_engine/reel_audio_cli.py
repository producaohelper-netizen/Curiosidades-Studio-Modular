"""Prepare phrase-synchronized Reels narration from already generated Piper WAVs.

Input JSON: {"segments":[{"text":"...","wav":"speech/001.wav"}, ...]}
Paths are relative to the input manifest directory. No voice is synthesized here.
"""
import argparse
import json
from pathlib import Path
from .reel_phrase_audio import join_phrase_wavs
from .reel_caption_timing import CaptionTimingError


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output-wav", required=True)
    ap.add_argument("--output-cues", required=True)
    args = ap.parse_args()
    try:
        manifest = Path(args.manifest).resolve()
        data = json.loads(manifest.read_text(encoding="utf8"))
        segments = data["segments"]
        if not isinstance(segments, list) or not segments:
            raise CaptionTimingError("Lista de segmentos ausente")
        pairs = []
        for item in segments:
            if not isinstance(item, dict) or not isinstance(item.get("wav"), str):
                raise CaptionTimingError("Manifesto contém segmento inválido")
            wav = (manifest.parent / item["wav"]).resolve()
            if not wav.is_relative_to(manifest.parent):
                raise CaptionTimingError("Caminho WAV fora da pasta do manifesto")
            pairs.append((item.get("text"), wav))
        timing = join_phrase_wavs(pairs, args.output_wav)
        target = Path(args.output_cues)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(timing, ensure_ascii=False, indent=2), encoding="utf8")
        print("Áudio e legendas por frase sincronizados a partir dos WAVs reais.")
    except (OSError, ValueError, KeyError, TypeError, CaptionTimingError) as exc:
        ap.exit(2, "Falha ao preparar narração curta: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
