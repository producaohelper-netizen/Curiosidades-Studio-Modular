"""Subtle organic deformation for unrigged 2D illustrations.

This is a fallback, NOT a replacement for articulated keyframes. Restrict to
original/cartoon artwork and animal silhouettes; avoid photographic distortions.
"""
from __future__ import annotations
import math
from PIL import Image

def organic_sway(image: Image.Image, time_sec: float, *,
                 strength: float = .029, cycle: float = 1.7):
    if image.mode != "RGBA":
        image=image.convert("RGBA")
    w,h=image.size
    if min(w,h)<12 or strength<=0:
        return image.copy()
    strength=min(.045,float(strength))
    mesh=[]
    step=max(3,h//32)
    for y0 in range(0,h,step):
        y1=min(h,y0+step)
        def displacement(y):
            yy=y/max(1,h)
            weight=max(0.,min(1.,(yy-.31)/.69))**1.55
            phase=time_sec*(2*math.pi/cycle)+yy*5.0
            return w*strength*weight*math.sin(phase)
        x0=displacement(y0);x1=displacement(y1)
        quad=(x0,y0,x1,y1,w+x1,y1,w+x0,y0)
        mesh.append(((0,y0,w,y1),quad))
    return image.transform((w,h),Image.Transform.MESH,mesh,
                           resample=Image.Resampling.BICUBIC,
                           fillcolor=(0,0,0,0))


def organic_swim(image: Image.Image, time_sec: float, *,
                 tail_side: str = "left", strength: float = .022):
    """Bend the tail end of a fish silhouette while preserving its head.

    Works with a single RGBA sprite, independently of subject or background.
    It is deliberately restrained; skeletal animation remains preferable.
    """
    if tail_side not in ("left","right"):
        raise ValueError("tail_side must be left or right")
    if image.mode != "RGBA":
        image=image.convert("RGBA")
    turn=(Image.Transpose.ROTATE_90 if tail_side=="left"
          else Image.Transpose.ROTATE_270)
    undo=(Image.Transpose.ROTATE_270 if tail_side=="left"
          else Image.Transpose.ROTATE_90)
    rotated=image.transpose(turn)
    swayed=organic_sway(rotated,time_sec,strength=strength,cycle=1.45)
    return swayed.transpose(undo)
