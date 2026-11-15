"""Subtle deterministic environmental animation for generic 2D scene settings.

No subject-specific code: underwater bubbles, drifting forest leaves, volcanic
ash and gentle space stars are setting-level layers. Their positions depend on
absolute seconds and SceneSpec identity, so rerendering a frame is repeatable.
"""
from __future__ import annotations
from PIL import Image,ImageDraw
import math,random,hashlib

def draw_environment(canvas:Image.Image, setting:str, t:float, identity:str="scene"):
    if canvas.mode!="RGBA":
        raise ValueError("Environment expects RGBA canvas")
    if not math.isfinite(t):raise ValueError("Time must be finite")
    kind=str(setting or "").lower()
    if kind not in {"underwater","forest","nature","space","volcanic","desert"}:
        return canvas
    w,h=canvas.size
    seed=int(hashlib.sha256((identity+"|"+kind).encode("utf8")).hexdigest()[:12],16)
    rng=random.Random(seed)
    d=ImageDraw.Draw(canvas,"RGBA")
    if kind=="underwater":
        # Independent bubbles slowly rise; subtle translucency doesn't hide fish.
        for i in range(22):
            bx=rng.uniform(.02,.98)*w
            by=rng.uniform(0,h)
            speed=rng.uniform(9,24)
            x=bx+math.sin(t*.45+i*.61)*w*.008
            y=(by-t*speed)%(h+55)-28
            rad=max(2,round(rng.uniform(.004,.016)*w))
            alpha=round(60+55*max(0,1-y/h))
            d.ellipse((x-rad,y-rad,x+rad,y+rad),
                      outline=(183,237,245,alpha),width=max(1,w//500))
        # Sparse shafts of light move gently, distinct from a camera zoom.
        for k in range(3):
            x=w*(.13+k*.33)+math.sin(t*.16+k)*w*.03
            d.polygon([(x-24,0),(x+12,0),(x+h*.18,h),(x-h*.04,h)],
                      fill=(170,219,243,10))
    elif kind in ("forest","nature"):
        for i in range(15):
            x=(rng.uniform(0,w)+t*rng.uniform(2,8))%(w+35)-15
            y=(rng.uniform(0,h)+t*rng.uniform(4,10))%(h+35)-15
            rr=max(2,round(w*rng.uniform(.003,.009)))
            d.ellipse((x-rr,y-rr/2,x+rr,y+rr/2),
                      fill=(193,216,115,80))
    elif kind=="volcanic":
        # Ash particles float upward and to the side. The mountain is still
        # drawn separately and remains the subject.
        for i in range(25):
            x=(rng.uniform(0,w)+t*rng.uniform(1,9))%w
            y=(rng.uniform(0,h)-t*rng.uniform(6,17))%h
            rr=max(1,round(w*rng.uniform(.002,.006)))
            d.ellipse((x-rr,y-rr,x+rr,y+rr),
                      fill=(210,187,176,round(rng.uniform(40,105))))
    elif kind=="space":
        for i in range(22):
            x=rng.uniform(.03,.97)*w
            y=rng.uniform(.03,.97)*h
            alpha=round(45+55*(1+math.sin(t*.7+i*2.2))*.5)
            rr=max(1,round(w*.0018))
            d.ellipse((x-rr,y-rr,x+rr,y+rr),
                      fill=(238,237,201,alpha))
    else:
        for i in range(10):
            x=(rng.uniform(0,w)+t*rng.uniform(1,5))%w
            y=rng.uniform(.45,.85)*h
            r=max(2,round(w*.003))
            d.ellipse((x-r,y-r/2,x+r,y+r/2),fill=(229,210,175,75))
    return canvas
