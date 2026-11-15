"""Verify a Windows candidate contains everything its Python entrypoint imports.

This is a packaging check, not a claim that a real episode has been generated.
"""
from __future__ import annotations
from pathlib import Path


REQUIRED = (
    "CuriosidadesStudio_Unificado_Windows_CANDIDATO.exe",
    "universal_engine/__init__.py",
    "universal_engine/production.py",
    "universal_engine/bootstrap.py",
    "universal_engine/layer_renderer.py",
    "universal_engine/mouth_overlay.py",
    "universal_engine/mouth_sync.py",
    "qa/video_integrity_audit.py",
    "requirements-local.txt",
)


def missing_files(root):
    root = Path(root)
    return [name for name in REQUIRED if not (root / name).is_file()]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    missing = missing_files(args.root)
    if missing:
        print("Pacote Windows incompleto:", ", ".join(missing))
        return 2
    print("Arquivos do candidato Windows verificados. Validacao real ainda pendente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
