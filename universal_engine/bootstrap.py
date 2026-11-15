"""First-run setup using only free local components.

Downloads a pinned published pt-BR Piper voice and installs free Python
packages only when missing. No antivirus bypass, hidden administrator action,
paid API, or unverified execution of downloaded scripts.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from urllib.request import Request, urlopen

VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium"
VOICE_NAME = "pt_BR-faber-medium.onnx"
DEPENDENCIES = {
    "PIL": "Pillow>=11,<13",
    "open_clip": "open_clip_torch",
    "rembg": "rembg[cpu]>=2.0.80",
    "cv2": "opencv-python-headless",
    "piper": "piper-tts",
}

class BootstrapError(RuntimeError):
    pass

def missing_packages():
    return [package for module,package in DEPENDENCIES.items()
            if importlib.util.find_spec(module) is None]

def install_missing(packages, runner=subprocess.run):
    if not packages: return []
    cmd=[sys.executable,"-m","pip","install","--disable-pip-version-check",*packages]
    result=runner(cmd,check=False)
    if result.returncode:
        raise BootstrapError(f"Falha instalando bibliotecas gratuitas, código {result.returncode}")
    return packages

def piper_executable():
    candidates=[shutil.which("piper"),
                str(Path(sysconfig.get_path("scripts"))/
                    ("piper.exe" if os.name=="nt" else "piper"))]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():return str(Path(candidate).resolve())
    raise BootstrapError("Comando Piper não foi instalado corretamente")

def download_model(model: Path, *, opener=urlopen):
    """Write to a temporary file and move only once integrity checks pass."""
    model.parent.mkdir(parents=True, exist_ok=True)
    cfg=Path(str(model)+".json")
    files=[(VOICE_NAME,model,30_000_000),(VOICE_NAME+".json",cfg,300)]
    for name,target,minimum in files:
        if target.exists() and target.stat().st_size>minimum:
            continue
        src=VOICE_BASE+"/"+name
        req=Request(src,headers={"User-Agent":"CuriosidadesStudio/1.0"})
        temporary=target.with_suffix(target.suffix+".partial")
        try:
            with opener(req,timeout=120) as response, temporary.open("wb") as f:
                total=0
                while True:
                    block=response.read(1024*1024)
                    if not block: break
                    total+=len(block)
                    if total>600_000_000:
                        raise BootstrapError("Arquivo excede limite de tamanho")
                    f.write(block)
            if temporary.stat().st_size<=minimum:
                raise BootstrapError(f"Download incompleto: {name}")
            if name.endswith(".json"):
                parsed=json.loads(temporary.read_text(encoding="utf8"))
                if not isinstance(parsed,dict) or "audio" not in parsed:
                    raise BootstrapError("Configuração de voz não é válida")
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    return model

def find_ffmpeg_bin(voice_path):
    if shutil.which('ffmpeg') and shutil.which('ffprobe'):
        return ''
    root=Path(voice_path).resolve().parent.parent
    for folder in (root/'tools',root/'bin'):
        if not folder.is_dir():continue
        for command in list(folder.rglob('ffmpeg.exe' if os.name=='nt' else 'ffmpeg'))[:40]:
            partner=command.parent/('ffprobe.exe' if os.name=='nt' else 'ffprobe')
            if partner.is_file():return str(command.parent)
    raise BootstrapError('FFmpeg/FFprobe não encontrados nas ferramentas do Studio')

def check_runtime(*, voice_path, packages=None, install=True, downloader=download_model):
    missing=missing_packages() if packages is None else packages
    if missing and not install:
        raise BootstrapError("Dependências não instaladas: "+", ".join(missing))
    if missing:install_missing(missing)
    ffmpeg_dir=find_ffmpeg_bin(voice_path)
    model=Path(voice_path)
    if not model.is_file() or not Path(str(model)+".json").is_file():
        downloader(model)
    voice=piper_executable()
    return {"piper":voice,"voice_model":str(model.resolve()),
            "ffmpeg_bin_dir":ffmpeg_dir,
            "python":sys.executable,"status":"ready_dependencies",
            "comfy_ui_art_assets":"still_requires_model_and_local_server",
            "ollama":"requires_preinstalled_local_model",
            "publisher_approval":"not_automated"}

def setup(workspace,voice_model=None):
    root=Path(workspace);root.mkdir(parents=True,exist_ok=True)
    model=Path(voice_model) if voice_model else root/"models"/VOICE_NAME
    result=check_runtime(voice_path=model)
    state=root/"runtime_configuration.json"
    tmp=state.with_suffix(".json.partial")
    tmp.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf8")
    tmp.replace(state)
    return state

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--voice-model")
    args=ap.parse_args()
    try: print(setup(args.workspace,args.voice_model))
    except Exception as exc:
        print(f"Falha de preparação: {exc}",file=sys.stderr)
        raise SystemExit(2)
