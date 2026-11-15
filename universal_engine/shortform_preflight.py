"""Validate a short-form episode brief before expensive voice and video generation.

Usage: python -m universal_engine.shortform_preflight --input roteiro_reel.json --output plano_reel.json
This is an editorial preflight, NOT a video renderer or independent source checker.
"""
import argparse
import json
from pathlib import Path
from .shortform import validate_reel, ShortFormError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.input)
    target = Path(args.output)
    try:
        draft = json.loads(source.read_text(encoding="utf8"))
        result = validate_reel(draft)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    except (OSError, ValueError, ShortFormError) as exc:
        parser.exit(2, "Roteiro curto rejeitado: " + str(exc) + "\n")
    print("Roteiro estruturado. Fontes ainda precisam de verificação independente; publicação bloqueada.")


if __name__ == "__main__":
    main()
