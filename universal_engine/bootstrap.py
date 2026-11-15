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
import time

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

def ensure_ollama(root,model="qwen2.5:7b",fetcher=None):
    """Start installed Ollama when stopped; pull model only if absent."""
    if fetcher is None:
        def fetcher():
            with urlopen("http://127.0.0.1:11434/api/tags",timeout=5) as response:
                return json.load(response)
    try:
        data=fetcher()
    except (OSError,ValueError):
        executable=shutil.which("ollama")
        if not executable and os.name=="nt":
            candidate=Path(os.environ.get("LOCALAPPDATA",""))/"Programs"/"Ollama"/"ollama.exe"
            if candidate.is_file():executable=str(candidate)
        if not executable:
            raise BootstrapError("Ollama não encontrado; instale o aplicativo gratuito")
        logfile=Path(root)/"logs"/"ollama-server.log"
        logfile.parent.mkdir(parents=True,exist_ok=True)
        with logfile.open("ab") as stream:
            options={"stdin":subprocess.DEVNULL,"stdout":stream,"stderr":stream}
            if os.name=="nt":
                options["creationflags"]=getattr(subprocess,"DETACHED_PROCESS",0x00000008)
            else:
                options["start_new_session"]=True
            subprocess.Popen([executable,"serve"],**options)
        data=None
        for i in range(25):
            time.sleep(1)
            try:
                data=fetcher();break
            except (OSError,ValueError):continue
        if data is None:raise BootstrapError("Ollama não iniciou em localhost:11434")
    names=[str(m.get("name") or m.get("model") or "") for m in data.get("models",[])]
    if model not in names:
        executable=shutil.which("ollama")
        if not executable and os.name=="nt":
            candidate=Path(os.environ.get("LOCALAPPDATA",""))/"Programs"/"Ollama"/"ollama.exe"
            if candidate.is_file():executable=str(candidate)
        if not executable:raise BootstrapError("Ollama está ativo, mas seu comando não está disponível")
        print("Baixando modelo gratuito Ollama ausente:",model,flush=True)
        result=subprocess.run([executable,"pull",model],check=False,timeout=7200)
        if result.returncode:
            raise BootstrapError("Não foi possível baixar o modelo Ollama "+model)
    return {"model":model,"endpoint":"http://127.0.0.1:11434","ready":True}

def setup(workspace,voice_model=None,ollama_model='qwen2.5:7b'):
    root=Path(workspace);root.mkdir(parents=True,exist_ok=True)
    model=Path(voice_model) if voice_model else root/"models"/VOICE_NAME
    result=check_runtime(voice_path=model)
    result['ollama']=ensure_ollama(root,model=ollama_model)
    state=root/"runtime_configuration.json"
    tmp=state.with_suffix(".json.partial")
    tmp.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf8")
    tmp.replace(state)
    return state

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--voice-model")
    ap.add_argument("--ollama-model",default="qwen2.5:7b")
    args=ap.parse_args()
    try: print(setup(args.workspace,args.voice_model,args.ollama_model))
    except Exception as exc:
        print(f"Falha de preparação: {exc}",file=sys.stderr)
        raise SystemExit(2)
