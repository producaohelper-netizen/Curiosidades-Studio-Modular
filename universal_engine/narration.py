"""Narração offline Piper com cache por fala e verificação de áudio.

Nenhuma saída muda o roteiro silenciosamente. A linha do tempo visual é
retimada para o áudio real, evitando o corte de frases observado nas versões
anteriores.
"""
from __future__ import annotations
import hashlib,json,subprocess,wave,math,copy
from pathlib import Path
from .scenespec import validate,SceneError

class NarrationError(RuntimeError):pass

def pcm_duration(path):
    with wave.open(str(path),"rb") as wav:
        if wav.getnframes()<=0 or wav.getframerate()<=0:
            raise NarrationError("WAV vazio")
        length=wav.getnframes()/wav.getframerate()
        if not .15<length<600:raise NarrationError("WAV tem duracao invalida")
        data=wav.readframes(min(8192,wav.getnframes()))
        if not data or all(b==0 for b in data):
            raise NarrationError("Amostra WAV silenciosa")
        return length

def text_key(text,model,backend="piper",length_scale=1.0):
    path=Path(model)
    if not path.exists() or path.stat().st_size<1000:
        raise NarrationError("Modelo de voz não encontrado")
    record={"text":text.strip(),"model":str(path.resolve()),
            "size":path.stat().st_size,"mtime_ns":path.stat().st_mtime_ns,
            "backend":backend,"length_scale":length_scale}
    return hashlib.sha256(json.dumps(record,sort_keys=True).encode("utf8")).hexdigest()

def generate_piper(text,model,output, *, executable="piper",length_scale=1.0,timeout=180):
    """Piper binary must be installed and the .onnx+.json model available."""
    if not isinstance(text,str) or len(text.strip())<4:
        raise NarrationError("Texto insuficiente para narração")
    key=text_key(text,model,length_scale=length_scale)
    target=Path(output);target.parent.mkdir(parents=True,exist_ok=True)
    state=target.with_suffix(".cache.json")
    if target.is_file() and state.is_file():
        try:
            cached=json.loads(state.read_text(encoding="utf8"))
            if cached["key"]==key:
                return {"path":str(target),"duration":pcm_duration(target),"reused":True}
        except (ValueError,KeyError,EOFError,wave.Error):
            pass
    if not Path(str(model)+".json").exists():
        raise NarrationError("Arquivo de configuração ONNX .json ausente")
    args=[str(executable),"--model",str(model),"--output_file",str(target),
          "--length_scale",str(length_scale)]
    try:
        result=subprocess.run(args,input=text,encoding="utf8",errors="replace",
                              capture_output=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as err:
        target.unlink(missing_ok=True)
        raise NarrationError("Piper indisponível ou excedeu o tempo") from err
    if result.returncode:
        target.unlink(missing_ok=True)
        raise NarrationError("Piper falhou: "+result.stderr[-450:])
    try:duration=pcm_duration(target)
    except (OSError,EOFError,wave.Error,NarrationError) as err:
        target.unlink(missing_ok=True)
        raise NarrationError("Piper produziu áudio inválido") from err
    state.write_text(json.dumps({"key":key,"duration":duration}),encoding="utf8")
    return {"path":str(target),"duration":duration,"reused":False}

def retime_to_audio(scene:dict,real_duration:float)->dict:
    validate(scene)
    if not isinstance(real_duration,(int,float)) or not math.isfinite(real_duration) or not 1<=real_duration<=60:
        raise NarrationError("Duração fora da faixa do SceneSpec")
    new=copy.deepcopy(scene)
    original=float(new["duration_target_seconds"])
    ratio=real_duration/original
    new["duration_target_seconds"]=round(real_duration,4)
    for event in new["timeline"]:
        event["at"]=min(real_duration-.02,round(event["at"]*ratio,4))
        if "duration" in event:
            event["duration"]=round(event["duration"]*ratio,4)
            event["duration"]=min(event["duration"],max(.001,real_duration-event["at"]))
    validate(new)
    return new
