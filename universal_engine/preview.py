"""Previsualizacao visual do SceneSpec — arte provisoria, nunca final para YouTube.

Aparelhamento para o QA: permite verificar que acoes produzem quadros
distintos antes de renderizar uma animacao com assets ilustrados reais.
"""
from pathlib import Path
import argparse, json, math
from PIL import Image, ImageDraw, ImageFont
try:
    from .scenespec import validate, motion
except ImportError:
    from scenespec import validate, motion

PALETTE = {"underwater": ("#0a3456", "#0c789a"), "space": ("#090f32", "#272b69"),
           "workshop": ("#26394c", "#456579")}
TYPE_COLOR = {"person":"#f6ba8a", "animal":"#ff9562", "object":"#ffda63",
              "planet":"#70c4fb", "organ":"#f47892","machine":"#8ad6c1",
              "building":"#e5c798","label":"#ffffff"}

def _lerp_color(a, b, p):
    aa=tuple(bytes.fromhex(a.lstrip("#")))
    bb=tuple(bytes.fromhex(b.lstrip("#")))
    return tuple(round(x+(y-x)*p) for x,y in zip(aa,bb))

def render(scene, at, size=(960,540)):
    validate(scene)
    w,h=size
    style=scene.get("setting",{}).get("kind","workshop")
    top,bottom=PALETTE.get(style,PALETTE["workshop"])
    im=Image.new("RGB",size)
    draw=ImageDraw.Draw(im)
    for y in range(h):
        draw.line([(0,y),(w,y)],fill=_lerp_color(top,bottom,y/max(1,h-1)))
    if style=="underwater":
        for i in range(13):
            x=int(w*(.04 + i*.075))
            draw.ellipse((x,h-65,x+8,h-57),fill="#38b7b8")
        draw.line((0,h-38,w,h-38),fill="#7da89a",width=3)
    elif style=="space":
        for i in range(45):
            x=(i*237+57)%w;y=(i*181+29)%h
            draw.ellipse((x,y,x+2,y+2),fill="#d4dffd")
    else:
        draw.rectangle((0,h-77,w,h),fill="#344d57")
        for i in range(0,w,90):
            draw.line((i,h-75,i+20,h),fill="#566a78",width=2)
    poses=motion(scene,at)
    font=ImageFont.load_default()
    for actor in scene["actors"]:
        id=actor["id"];pose=poses[id]
        x=int(pose["x"]*w);y=int(pose["y"]*h);radius=int(37*pose["scale"])
        col=TYPE_COLOR[actor["kind"]]
        if actor["kind"] in ("animal","person"):
            draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=col,outline="#25334a",width=4)
            draw.ellipse((x+radius*.22,y-radius*.22,x+radius*.33,y-radius*.11),fill="#192333")
        elif actor["kind"]=="planet":
            draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=col,outline="#fff4bd",width=3)
            draw.arc((x-radius-16,y-radius*.5,x+radius+16,y+radius*.5),15,165,fill="#cde4ff",width=3)
        elif actor["kind"]=="machine":
            draw.rounded_rectangle((x-radius,y-radius,x+radius,y+radius),radius=9,fill=col,outline="#243746",width=4)
            draw.ellipse((x-16,y-10,x-7,y-1),fill="#26364b")
            draw.ellipse((x+7,y-10,x+16,y-1),fill="#26364b")
        else:
            draw.rounded_rectangle((x-radius,y-radius,x+radius,y+radius),radius=14,fill=col,outline="#243746",width=4)
        if pose["highlight"]:
            draw.ellipse((x-radius-9,y-radius-9,x+radius+9,y+radius+9),outline="#fff57c",width=5)
        if pose["effect"]:
            for z in range(8):
                theta=z*math.pi/4
                ex=x+math.cos(theta)*(radius+25);ey=y+math.sin(theta)*(radius+25)
                draw.ellipse((ex-6,ey-6,ex+6,ey+6),fill="#8666cc" if "ink" in pose["effect"] else "#ffffff")
        label=f"{id} · {pose['emotion']}" if pose["emotion"]!="neutral" else id
        box=draw.textbbox((0,0),label,font=font)
        tw=box[2]-box[0]
        draw.rounded_rectangle((x-tw/2-10,y+radius+9,x+tw/2+10,y+radius+31),radius=6,fill="#101b34")
        draw.text((x-tw/2,y+radius+14),label,fill="white",font=font)
    draw.rounded_rectangle((24,18,w-24,61),radius=10,fill="#101d36")
    title=scene.get("visual_fact","")
    draw.text((40,34),title[:110],fill="white",font=font)
    draw.text((w-100,h-28),f"{at:.2f}s",fill="white",font=font)
    return im

def contact_sheet(scene, destination, frames=9):
    from PIL import ImageOps
    validate(scene)
    frames=max(2,int(frames))
    w,h=480,270
    cols=3;rows=math.ceil(frames/cols)
    sheet=Image.new("RGB",(w*cols,h*rows))
    dur=scene["duration_target_seconds"]
    for index in range(frames):
        at=dur*index/frames
        img=render(scene,at,(w,h))
        sheet.paste(img,((index%cols)*w,(index//cols)*h))
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(destination,quality=88)
    return destination

def main():
    p=argparse.ArgumentParser()
    p.add_argument("scene_json");p.add_argument("output")
    args=p.parse_args()
    scene=json.loads(Path(args.scene_json).read_text(encoding="utf8"))
    print(contact_sheet(scene,args.output))
if __name__=="__main__":main()
