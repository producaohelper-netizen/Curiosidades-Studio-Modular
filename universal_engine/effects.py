"""Reusable drawn VFX for illustrated educational scenes.

Effects are derived from the action timeline and remain deterministic for a
given timestamp; no random per-frame flashing or movie stock assets.
"""
from PIL import ImageDraw
import math
import random

def paint_effect(canvas, effect, x, y, radius, age, identity=""):
    draw=ImageDraw.Draw(canvas,"RGBA")
    age=max(0.0,float(age))
    radius=max(8,int(radius))
    name=str(effect).casefold()
    rng=random.Random(identity+"|"+name)
    if "ink" in name or "tinta" in name:
        growth=min(1.0,age/1.2)
        if growth<=0:return
        cloud=radius*(.25+growth*1.65)
        alpha=round(180*max(.25,1-age/4.5))
        for i in range(16):
            theta=i*2.4
            offset=(.26+.56*(i%5)/5)*cloud
            ox=math.cos(theta)*offset
            oy=math.sin(theta)*offset*.74
            size=cloud*(.18+.14*((i*7)%5)/5)
            draw.ellipse((x+ox-size,y+oy-size,x+ox+size,y+oy+size),
                         fill=(49,24,86,alpha))
    elif any(v in name for v in ("smoke","eruption","vulc","lava")):
        growth=min(1.0,age/2)
        for i in range(16):
            drift=math.sin(i*1.7+age*.9)*radius*.2
            rise=radius*(.3+i*.13+min(age,3)*.32)
            rr=radius*(.10+.10*(i%4)/4)*(.7+growth)
            xx=x+drift+math.cos(i*2.9)*radius*.18
            yy=y-rise
            tone=(105+i*7)%55+78
            draw.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),
                         fill=(tone,tone-8,tone-2,round(165*max(.4,1-age/7))))
        for i in range(14):
            theta=i*2.4
            rr=radius*.025
            dx=(i%7-3)*radius*.15+math.sin(theta+age)*radius*.12
            dy=-(age*.8+i*.11)*radius+math.cos(theta)*radius*.14
            draw.ellipse((x+dx-rr,y+dy-rr,x+dx+rr,y+dy+rr),
                         fill=(255,122+(i%3)*25,30,225))
    else:
        for i in range(9):
            theta=i*2.4+age*.6
            distance=radius*(.7+min(age,2)*.35)
            xx=x+math.cos(theta)*distance
            yy=y+math.sin(theta)*distance
            rr=max(2,round(radius*.055))
            draw.line((xx-rr,yy,xx+rr,yy),fill=(255,236,140,220),width=3)
            draw.line((xx,yy-rr,xx,yy+rr),fill=(255,236,140,220),width=3)
