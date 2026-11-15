"""Comparação visual auditável entre amostra e episódio gerado.

Amostras extraídas em intervalos equivalentes, sem copiar a obra de referência.
As métricas não determinam qualidade artística: divergência de tema, animação,
coerência e legibilidade exigem avaliação humana.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def metadata(path):
    raw=subprocess.check_output(["ffprobe","-v","error",
        "-show_entries","format=duration:stream=width,height",
        "-of","json",str(path)],text=True)
    result=json.loads(raw)
    duration=float(result["format"]["duration"])
    stream=next(s for s in result.get("streams",[]) if "width" in s)
    return duration,(stream["width"],stream["height"])


def snapshot(video,second,size=(360,203)):
    raw=subprocess.check_output([
       "ffmpeg","-hide_banner","-loglevel","error","-ss",str(second),
       "-i",str(video),"-frames:v","1",
       "-vf",f"scale={size[0]}:{size[1]}:flags=lanczos",
       "-f","image2pipe","-vcodec","png","-"
    ])
    with Image.open(BytesIO(raw)) as image:
        return image.convert("RGB")


def contact_sheet(reference,produced,output,frames=12):
    reference=Path(reference);produced=Path(produced)
    if not reference.is_file() or not produced.is_file():
        raise FileNotFoundError("Amostra ou vídeo produzido ausente")
    rdur,rs=metadata(reference);pdur,ps=metadata(produced)
    cols=4;w,h=360,203;heading=28
    rows=math.ceil(frames/cols)
    sheet=Image.new("RGB",(cols*w,2*rows*(h+heading)),(16,26,40))
    d=ImageDraw.Draw(sheet)
    labels=[("Referência do usuário",reference,rdur),
            ("Produção local",produced,pdur)]
    for ridx,(label,video,dur) in enumerate(labels):
        for i in range(frames):
            seconds=max(0.1,(i+.5)/frames*dur)
            img=snapshot(video,seconds,(w,h))
            x=i%cols*w;y=(ridx*rows+i//cols)*(h+heading)
            d.text((x+8,y+6),f"{label}: {seconds:.0f}s",fill="white")
            sheet.paste(img,(x,y+heading))
    dst=Path(output);dst.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(dst,quality=89)
    data={"reference":{"duration":rdur,"resolution":rs},
          "produced":{"duration":pdur,"resolution":ps},
          "frames_per_video":frames,
          "visual_side_by_side":str(dst),
          "narration_image_coherence":"REQUIRES_HUMAN_REVIEW",
          "cartoon_character_consistency":"REQUIRES_HUMAN_REVIEW",
          "creative_quality":"NOT_AUTOMATICALLY_APPROVED"}
    dst.with_suffix(".json").write_text(json.dumps(data,indent=2,ensure_ascii=False),
                                       encoding="utf8")
    return data


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("reference")
    p.add_argument("produced")
    p.add_argument("output")
    p.add_argument("--frames",type=int,default=12)
    args=p.parse_args()
    print(json.dumps(contact_sheet(args.reference,args.produced,args.output,
                                   frames=args.frames),ensure_ascii=False,indent=2))
