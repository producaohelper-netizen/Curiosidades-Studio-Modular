"""Renderizador 2D por camadas, independente do tema.

Exige PNGs transparentes de atores e um fundo coerente. Não fabrica atores com
círculos genéricos quando o modo de produção está ativo. Usa SceneSpec para
posicionar e movimentar os elementos visuais ao longo da narração.
"""
from __future__ import annotations
from PIL import Image, ImageDraw
from pathlib import Path
from io import BytesIO
import math, subprocess, wave, json
from .scenespec import validate, motion
from .camera import apply_camera

class RenderError(RuntimeError):
    pass

def cover(image:Image.Image, size:tuple[int,int]):
    """Fill canvas without stretching aspect ratio."""
    w,h=size
    factor=max(w/image.width,h/image.height)
    nw=max(w,round(image.width*factor));nh=max(h,round(image.height*factor))
    image=image.resize((nw,nh),Image.Resampling.LANCZOS)
    left=(nw-w)//2;top=(nh-h)//2
    return image.crop((left,top,left+w,top+h))

def render_frame(scene:dict, time_sec:float, background:Image.Image,
                 assets:dict[str,Image.Image], size=(960,540),
                 *, missing_is_error:bool=True) -> Image.Image:
    validate(scene)
    w,h=size
    if not isinstance(background,Image.Image):
        raise RenderError("Cenario de fundo ausente")
    canvas=cover(background.convert("RGBA"),size)
    poses=motion(scene,time_sec)
    for actor in scene["actors"]:
        name=actor["id"]
        img=assets.get(actor["asset_id"])
        if img is None:
            if missing_is_error:raise RenderError("PNG RGBA ausente: "+actor["asset_id"])
            continue
        transform=poses[name]
        if float(transform.get("opacity",1))<=0:continue
        layer=img.convert("RGBA")
        scale=float(transform["scale"])*float(actor.get("size",.28))
        px=max(1,int(w*scale))
        py=max(1,int(px*layer.height/layer.width))
        layer=layer.resize((px,py),Image.Resampling.LANCZOS)
        if abs(transform["angle"])>0.1:
            layer=layer.rotate(-float(transform["angle"]),resample=Image.Resampling.BICUBIC,expand=True)
        alpha=float(transform.get("opacity",1))
        if alpha<1:
            layer.putalpha(layer.getchannel("A").point(lambda x:int(x*alpha)))
        pos=(int(transform["x"]*w-layer.width*.5),
             int(transform["y"]*h-layer.height*.5))
        canvas.alpha_composite(layer,pos)
        if transform.get("highlight"):
            d=ImageDraw.Draw(canvas)
            x=int(transform["x"]*w);y=int(transform["y"]*h)
            d.ellipse((x-px*.6,y-py*.6,x+px*.6,y+py*.6),
                      outline="#fbe671",width=max(2,w//300))
        if transform.get("effect"):
            d=ImageDraw.Draw(canvas)
            x=int(transform["x"]*w);y=int(transform["y"]*h)
            for n in range(14):
                theta=n*math.pi*2/14
                distance=px*.54+(time_sec%1)*px*.20
                ex=int(x+distance*math.cos(theta))
                ey=int(y+distance*math.sin(theta))
                radius=max(2,w//150)
                d.ellipse((ex-radius,ey-radius,ex+radius,ey+radius),
                          fill="#4d3b78" if "ink" in str(transform["effect"]) else "#eac959")
    return apply_camera(canvas.convert("RGB"),scene,time_sec,poses)

def audio_duration(path:str|Path) -> float:
    """PCM WAV only, preserving exact recorded speech duration."""
    with wave.open(str(path),"rb") as wav:
        if wav.getnframes()<=0:raise RenderError("Audio WAV vazio")
        return wav.getnframes()/wav.getframerate()

def render_clip(scene:dict, background_path:str|Path, asset_paths:dict[str,str|Path],
                wav_path:str|Path, output_path:str|Path, *,
                fps:int=24, size=(960,540), ffmpeg="ffmpeg"):
    validate(scene)
    if not 8<=fps<=30:raise RenderError("FPS fora da faixa permitida")
    background=Image.open(background_path).convert("RGBA")
    layers={name:Image.open(p).convert("RGBA") for name,p in asset_paths.items()}
    for actor in scene["actors"]:
        if actor["asset_id"] not in layers:
            raise RenderError("Actor sem asset: "+actor["asset_id"])
    length=audio_duration(wav_path)
    if abs(length-float(scene["duration_target_seconds"]))>5:
        raise RenderError("A duracao narrada diverge do planejamento em mais de 5s")
    count=math.ceil(length*fps)
    out=Path(output_path);out.parent.mkdir(parents=True,exist_ok=True)
    args=[ffmpeg,"-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24",
          "-s",f"{size[0]}x{size[1]}","-r",str(fps),"-i","pipe:0",
          "-i",str(wav_path),"-map","0:v:0","-map","1:a:0",
          "-c:v","libx264","-preset","ultrafast","-crf","22",
          "-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
          "-t",f"{length:.4f}","-movflags","+faststart",str(out)]
    proc=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for i in range(count):
            frame=render_frame(scene,i/fps,background,layers,size)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        error=proc.stderr.read()
        returncode=proc.wait()
        if returncode!=0:
            raise RenderError("FFmpeg falhou: "+error.decode("utf8","replace")[-1000:])
    except Exception:
        if proc.poll() is None:proc.kill();proc.wait()
        out.unlink(missing_ok=True)
        raise
    finally:
        background.close()
        for layer in layers.values():layer.close()
    if not out.exists() or out.stat().st_size<1024:
        raise RenderError("MP4 ausente ou vazio")
    return {"output":str(out),"duration":length,"frames":count,
            "size":list(size),"fps":fps,"scene_id":scene["scene_id"]}
