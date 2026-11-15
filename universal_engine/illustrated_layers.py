"""Reusable original illustrated backdrops plus transparent Wikimedia sprites.

No destructive hole-filling: a vector/PNG character with transparency is
composited on an independent illustrated setting. Works on CPU.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
import random

BACKGROUNDS={
    "underwater":("#07355b","#1e94ad","#44b8c4"),
    "space":("#070b24","#192457","#4f477f"),
    "forest":("#183b49","#568e61","#afbe77"),
    "workshop":("#293c50","#65808f","#b3b2a3"),
    "nature":("#133c54","#6e9b73","#a4bd91"),
    "desert":("#6b4a5d","#cd9671","#e4bb85"),
    "history":("#49475c","#b49779","#d0b88e"),
    "volcanic":("#273147","#6c6069","#b0896f"),
}
DEFAULT=("#172b48","#557b8d","#a0adb0")

class IllustratedLayerError(RuntimeError):
    pass

def has_alpha(path):
    with Image.open(path) as im:
        if "A" not in im.convert("RGBA").getbands():return False
        alpha=im.convert("RGBA").getchannel("A")
        return alpha.getextrema()[0]<240 and alpha.getextrema()[1]>20

def alpha_sprite(source,destination):
    source=Path(source);destination=Path(destination)
    with Image.open(source) as original:
        frame=original.convert("RGBA")
        alpha=frame.getchannel("A")
        low,high=alpha.getextrema()
        if low>=240 or high<20:
            raise IllustratedLayerError("Ilustração não contém personagem transparente")
        box=alpha.point(lambda v:255 if v>20 else 0).getbbox()
        if not box:raise IllustratedLayerError("Ilustração vazia")
        occupied=sum(alpha.histogram()[128:])/max(1,alpha.width*alpha.height)
        if occupied<.006 or occupied>.89:
            raise IllustratedLayerError("Máscara de personagem com proporções suspeitas")
        pad=max(4,round(min(frame.size)*.025))
        l,t,r,b=box
        box=(max(0,l-pad),max(0,t-pad),
             min(frame.width,r+pad),min(frame.height,b+pad))
        cropped=frame.crop(box)
        destination.parent.mkdir(parents=True,exist_ok=True)
        cropped.save(destination,"PNG")
    return destination

def _rgb(h):
    h=h.lstrip("#")
    return tuple(int(h[x:x+2],16) for x in (0,2,4))

def create_background(kind, output, *, size=(1280,720), identity="default"):
    w,h=size
    if w<=0 or h<=0:raise IllustratedLayerError("Tamanho inválido")
    a,b,c=map(_rgb,BACKGROUNDS.get(kind,DEFAULT))
    canvas=Image.new("RGB",(w,h)); draw=ImageDraw.Draw(canvas)
    for y in range(h):
        ratio=y/max(1,h-1)
        if ratio<.65:
            z=ratio/.65; start,end=a,b
        else:
            z=(ratio-.65)/.35;start,end=b,c
        col=tuple(round(v+(q-v)*z) for v,q in zip(start,end))
        draw.line((0,y,w,y),fill=col)
    # Subtle original geometric environment. Deliberately less visually busy
    # than the subject, avoids photographic filler and unwanted typography.
    rng=random.Random(identity+"|"+kind)
    if kind=="space":
        for i in range(115):
            x=rng.randrange(w);y=rng.randrange(h)
            radius=rng.choice([1,1,2,3])
            draw.ellipse((x-radius,y-radius,x+radius,y+radius),
                         fill=rng.choice(["#d8dded","#9cbee6","#f2c981"]))
    elif kind=="underwater":
        draw.ellipse((-w//4,h-h//7,w//2,h+h//5),fill="#146080")
        draw.ellipse((w//2,h-h//8,w+w//5,h+h//3),fill="#12536a")
        for i in range(28):
            x=rng.randrange(w);y=rng.randrange(h)
            rad=rng.randrange(5,22)
            draw.ellipse((x-rad,y-rad,x+rad,y+rad),
                         outline="#76bdcc",width=2)
    elif kind=="volcanic":
        # Original rocky terrain suitable for volcanoes, geology and eruptions,
        # leaving the centre free for the featured subject.
        draw.polygon([(0,int(h*.67)),(int(w*.14),int(h*.39)),
                      (int(w*.32),int(h*.69)),(int(w*.48),int(h*.53)),
                      (int(w*.65),int(h*.70)),(w,int(h*.60)),(w,h),(0,h)],
                     fill="#62565d")
        draw.polygon([(0,int(h*.76)),(int(w*.16),int(h*.59)),
                      (int(w*.34),int(h*.86)),(int(w*.53),int(h*.76)),
                      (int(w*.78),int(h*.82)),(w,int(h*.73)),(w,h),(0,h)],
                     fill="#504951")
        for i in range(11):
            x=rng.randrange(w)
            y=rng.randrange(int(h*.73),h)
            rr=rng.randrange(max(3,w//180),max(8,w//55))
            draw.ellipse((x-rr,y-rr//2,x+rr,y+rr//2),fill="#6a6263")
    elif kind in ("forest","nature"):
        draw.ellipse((-w//5,h*.55,w*.7,h*1.35),fill="#366b60")
        draw.ellipse((w*.4,h*.61,w*1.3,h*1.4),fill="#2c655d")
        for i in range(8):
            x=int((i+.2)*w/8)
            draw.rounded_rectangle((x,h*.23,x+max(8,w//50),h*.81),
                                   radius=3,fill="#2f5550")
            draw.ellipse((x-w*.055,h*.1,x+w*.07,h*.53),fill="#3c8571")
    else:
        for i in range(8):
            yy=int(h*(.66+i*.07))
            draw.line((0,yy,w,yy),fill="#ffffff",width=1)
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(dest,"PNG")
    return dest
