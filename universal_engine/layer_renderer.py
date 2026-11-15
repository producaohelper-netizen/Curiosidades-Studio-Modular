"""Renderizador 2D por camadas, independente do tema.

Exige PNGs transparentes de atores e um fundo coerente. Não fabrica atores com
círculos genéricos quando o modo de produção está ativo. Usa SceneSpec para
posicionar e movimentar os elementos visuais ao longo da narração.
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from io import BytesIO
import math, subprocess, wave, json
from .scenespec import validate, motion
from .camera import apply_camera
from .sprites import select_frame
from .effects import paint_effect
from .deformation import organic_sway

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
                 *, missing_is_error:bool=True,layer_cache=None) -> Image.Image:
    validate(scene)
    w,h=size
    if not isinstance(background,Image.Image):
        raise RenderError("Cenario de fundo ausente")
    canvas=background.copy() if background.mode=="RGBA" and background.size==size else cover(background.convert("RGBA"),size)
    poses=motion(scene,time_sec)
    for actor in scene["actors"]:
        name=actor["id"]
        img=assets.get(actor["asset_id"])
        if img is None:
            if missing_is_error:raise RenderError("PNG RGBA ausente: "+actor["asset_id"])
            continue
        transform=poses[name]
        if float(transform.get("opacity",1))<=0:continue
        sheet=actor.get("sprite")
        if sheet is not None:
            img=select_frame(img,time_sec,rows=sheet["rows"],columns=sheet["columns"],
                             frames=sheet["frames"],pose_fps=float(sheet.get("fps",8)),
                             loop=bool(sheet.get("loop",True)))
        source=img.convert("RGBA")
        scale=float(transform["scale"])*float(actor.get("size",.28))
        px=max(1,int(w*scale))
        py=max(1,int(px*source.height/source.width))
        angle=round(float(transform["angle"]),1)
        key=(actor["asset_id"],id(img),px,py,angle)
        if layer_cache is not None and key in layer_cache:
            layer=layer_cache[key].copy()
        else:
            layer=source.resize((px,py),Image.Resampling.LANCZOS)
            if abs(angle)>0.1:
                layer=layer.rotate(-angle,resample=Image.Resampling.BICUBIC,expand=True)
            if layer_cache is not None and len(layer_cache)<120:
                layer_cache[key]=layer.copy()
        if (actor.get("kind")=="animal" and sheet is None and
            scene.get("visual_style")=="cartoon" and actor.get("organic_sway",True)):
            layer=organic_sway(layer,time_sec)
        alpha=float(transform.get("opacity",1))
        if alpha<1:
            layer.putalpha(layer.getchannel("A").point(lambda x:int(x*alpha)))
        pos=(int(transform["x"]*w-layer.width*.5),
             int(transform["y"]*h-layer.height*.5))
        # Effects belong behind actors, at a bounded, meaningful origin.
        # Formerly an ink cloud 2x the sprite width obscured the entire scene.
        if transform.get("effect"):
            effect=str(transform["effect"])
            ink=("ink" in effect.casefold() or "tinta" in effect.casefold())
            volcanic=any(v in effect.casefold() for v in
                         ("smoke","eruption","vulc","lava"))
            ex=int(transform["x"]*w+(px*.2 if ink else 0))
            ey=int(transform["y"]*h-(py*.30 if volcanic else 0))
            radius=max(9,int(min(px*.23,w*.10)))
            paint_effect(canvas,effect,ex,ey,radius,
                         transform.get("effect_elapsed",0),name)
        canvas.alpha_composite(layer,pos)
        if transform.get("highlight"):
            d=ImageDraw.Draw(canvas)
            x=int(transform["x"]*w);y=int(transform["y"]*h)
            d.ellipse((x-px*.6,y-py*.6,x+px*.6,y+py*.6),
                      outline="#fbe671",width=max(2,w//300))
    # Uma palavra-chave discreta reforça a explicação sem virar slide estático.
    callout=scene.get("callout","")
    if isinstance(callout,str) and 1<=len(callout)<=45 and time_sec>=.45:
        d=ImageDraw.Draw(canvas,"RGBA")
        try:
            font=ImageFont.truetype("DejaVuSans-Bold.ttf",max(17,round(h*.044)))
        except OSError:
            font=ImageFont.load_default()
        words=callout.upper()
        l,t,r,b=d.textbbox((0,0),words,font=font)
        tw=r-l
        x=max(16,(w-tw)//2)
        y=h-max(70,round(h*.13))
        a=int(205*min(1.,(time_sec-.45)/.3))
        d.rounded_rectangle((x-24,y-12,x+tw+24,y+b-t+17),
                            radius=17,fill=(15,32,53,a),
                            outline=(232,242,250,min(160,a)),width=2)
        d.text((x,y),words,font=font,fill=(255,255,255,min(255,a+40)))
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
    background=cover(Image.open(background_path).convert("RGBA"),size)
    layer_cache={}
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
            frame=render_frame(scene,i/fps,background,layers,size,layer_cache=layer_cache)
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
