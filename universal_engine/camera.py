"""Cinematografia automática discreta, ligada a eventos do roteiro visual."""
from PIL import Image
import math

def camera_transform(scene, at, positions=None):
    """Return zoom and normalized camera center, never sudden discontinuities."""
    zoom=1.0;center=(.5,.5)
    actor_positions=positions or {}
    for step in scene.get("timeline",[]):
        if step.get("action") not in ("camera_push","camera_pan"):continue
        start=float(step.get("at",0))
        if at<start:break
        duration=max(.1,float(step.get("duration",.7)))
        u=max(0.,min(1.,(at-start)/duration))
        u=u*u*(3-2*u)
        if step["action"]=="camera_push":
            focus=actor_positions.get(step.get("target"),{})
            to_center=(float(focus.get("x",.5)),float(focus.get("y",.5)))
            strength=max(1.,min(1.8,float(step.get("zoom",1.25))))
            zoom=1+(strength-1)*u
            center=(.5+(to_center[0]-.5)*u*.65,
                    .5+(to_center[1]-.5)*u*.65)
        elif step["action"]=="camera_pan":
            center=(.5+(float(step.get("to_x",.5))-.5)*u*.65,
                    .5+(float(step.get("to_y",.5))-.5)*u*.65)
    return zoom,center

def apply_camera(image:Image.Image, scene, at, positions=None):
    zoom,center=camera_transform(scene,at,positions)
    if zoom<=1.0001 and center==(.5,.5):return image
    w,h=image.size
    cw=max(2,int(w/zoom));ch=max(2,int(h/zoom))
    cx=max(cw/2,min(w-cw/2,float(center[0])*w))
    cy=max(ch/2,min(h-ch/2,float(center[1])*h))
    left=int(cx-cw/2);top=int(cy-ch/2)
    crop=image.crop((left,top,left+cw,top+ch))
    return crop.resize((w,h),Image.Resampling.BICUBIC)
