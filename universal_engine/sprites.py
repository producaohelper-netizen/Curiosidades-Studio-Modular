"""Recorta quadros de uma folha de sprites reutilizando a mesma identidade visual."""
from PIL import Image
import math

class SpriteError(ValueError):pass

def select_frame(sheet:Image.Image, time_sec:float, *,
                 rows:int, columns:int, frames:int,
                 pose_fps:float=8., loop:bool=True)->Image.Image:
    if any(not isinstance(x,int) or x<=0 for x in (rows,columns,frames)):
        raise SpriteError("Grade inválida")
    if frames>rows*columns:raise SpriteError("Quadros excedem células da grade")
    if sheet.width%columns or sheet.height%rows:
        raise SpriteError("Spritesheet exige células de mesmo tamanho")
    if pose_fps<=0 or not math.isfinite(pose_fps):
        raise SpriteError("FPS de poses inválido")
    index=int(max(0.,time_sec)*pose_fps)
    if loop:index%=frames
    else:index=min(frames-1,index)
    x=index%columns;y=index//columns
    w=sheet.width//columns;h=sheet.height//rows
    return sheet.crop((x*w,y*h,(x+1)*w,(y+1)*h))
