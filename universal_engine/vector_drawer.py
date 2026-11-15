"""CPU-only vector illustration by a local text LLM and Pillow.

The model generates *validated drawing instructions*, NOT executable Python or
arbitrary SVG/HTML. Only allowlisted geometric primitives reach the renderer.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.request import Request,urlopen
from PIL import Image,ImageDraw

COLOR=re.compile(r"^#[0-9a-fA-F]{6}$")
SHAPES={"ellipse","rectangle","rounded_rectangle","polygon","line","arc"}
class VectorArtError(RuntimeError):pass

def _point(value):
    return (isinstance(value,(int,float)) and math.isfinite(value)
            and -12<=value<=524)

def validate_art(data):
    if not isinstance(data,dict):raise VectorArtError("Desenho não é objeto JSON")
    items=data.get("elements")
    if not isinstance(items,list) or not 7<=len(items)<=120:
        raise VectorArtError("Ilustração exige 7–120 elementos geométricos")
    for i,shape in enumerate(items):
        if not isinstance(shape,dict) or shape.get("shape") not in SHAPES:
            raise VectorArtError(f"Forma {i} não suportada")
        name=shape["shape"]
        for prop in ("fill","stroke"):
            color=shape.get(prop)
            if color is not None and (not isinstance(color,str) or not COLOR.fullmatch(color)):
                raise VectorArtError("Cor inválida; use #RRGGBB")
        if not shape.get("fill") and not shape.get("stroke"):
            raise VectorArtError("Forma sem cor")
        width=shape.get("width",4)
        if not isinstance(width,(int,float)) or not 0<width<=20:
            raise VectorArtError("Largura de contorno inválida")
        if name in ("ellipse","rectangle","rounded_rectangle","arc"):
            bbox=shape.get("bbox")
            if not isinstance(bbox,list) or len(bbox)!=4 or not all(_point(x) for x in bbox):
                raise VectorArtError("Retângulo delimitador inválido")
            if bbox[2]<=bbox[0] or bbox[3]<=bbox[1]:
                raise VectorArtError("Retângulo invertido")
            if name=="arc":
                if not all(isinstance(shape.get(q),(int,float)) and
                           math.isfinite(shape[q]) and -720<=shape[q]<=720
                           for q in ("start","end")):
                    raise VectorArtError("Arco inválido")
        elif name in ("polygon","line"):
            pts=shape.get("points")
            if (not isinstance(pts,list) or not 2<=len(pts)<=80 or
                (name=="polygon" and len(pts)<3) or
                any(not isinstance(p,list) or len(p)!=2 or
                    not all(_point(coord) for coord in p) for p in pts)):
                raise VectorArtError("Pontos inválidos")
    return data

def rasterize(data,output,size=512,supersample=2):
    validate_art(data)
    if not 256<=size<=1024 or supersample not in (1,2,3):
        raise VectorArtError("Resolução fora dos limites")
    ratio=size/512*supersample
    canvas=Image.new("RGBA",(size*supersample,size*supersample),(0,0,0,0))
    draw=ImageDraw.Draw(canvas)
    for sh in data["elements"]:
        name=sh["shape"]
        fill=sh.get("fill")
        outline=sh.get("stroke")
        width=max(1,round(sh.get("width",4)*ratio))
        if name in ("ellipse","rectangle","rounded_rectangle","arc"):
            coords=tuple(round(z*ratio) for z in sh["bbox"])
            if name=="ellipse":
                draw.ellipse(coords,fill=fill,outline=outline,width=width)
            elif name=="rectangle":
                draw.rectangle(coords,fill=fill,outline=outline,width=width)
            elif name=="rounded_rectangle":
                draw.rounded_rectangle(coords,radius=round(sh.get("radius",12)*ratio),
                                       fill=fill,outline=outline,width=width)
            else:
                draw.arc(coords,start=sh["start"],end=sh["end"],
                         fill=outline or fill,width=width)
        else:
            pts=[tuple(round(z*ratio) for z in p) for p in sh["points"]]
            if name=="polygon":
                draw.polygon(pts,fill=fill)
                if outline:
                    draw.line(pts+[pts[0]],fill=outline,width=width,joint="curve")
            else:
                draw.line(pts,fill=outline or fill,width=width,joint="curve")
    if supersample>1:
        canvas=canvas.resize((size,size),Image.Resampling.LANCZOS)
    alpha=canvas.getchannel("A")
    occupancy=sum(alpha.histogram()[128:])/(size*size)
    if not .012<occupancy<.88:
        raise VectorArtError(f"Desenho incompleto ou preenchido demais: {occupancy:.1%}")
    box=alpha.point(lambda x:255 if x>25 else 0).getbbox()
    if not box:raise VectorArtError("Desenho vazio")
    pad=12
    l,t,r,b=box
    cropped=canvas.crop((max(0,l-pad),max(0,t-pad),
                         min(size,r+pad),min(size,b+pad)))
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    cropped.save(out,"PNG")
    return out

def normalize_simple_shapes(data):
    """Repair only harmless axis inversions; reject missing or unsafe shapes."""
    if not isinstance(data,dict) or not isinstance(data.get("e"),list):
        raise VectorArtError("Desenho sem lista de formas")
    items=[]
    for n,shape in enumerate(data["e"]):
        if not isinstance(shape,dict) or shape.get("t") not in ("ellipse","rectangle"):
            raise VectorArtError(f"Forma {n}: tipo desconhecido")
        box=shape.get("b")
        if (not isinstance(box,list) or len(box)!=4 or
            not all(isinstance(x,(int,float)) and math.isfinite(x) for x in box)):
            raise VectorArtError(f"Forma {n}: coordenadas ausentes ou não numéricas")
        # Repair only bounded drawing mistakes: reorder inverted axes and
        # clip coordinates to the 512px artboard. Do not invent missing parts.
        if any(x < -64 or x > 576 for x in box):
            raise VectorArtError(f"Forma {n}: coordenadas fora do desenho")
        x1,x2=sorted((max(0.,min(512.,box[0])),max(0.,min(512.,box[2]))))
        y1,y2=sorted((max(0.,min(512.,box[1])),max(0.,min(512.,box[3]))))
        if x2-x1<2 or y2-y1<2:
            raise VectorArtError(f"Forma {n}: dimensões inválidas")
        fill=shape.get("f");stroke=shape.get("s")
        if not all(isinstance(v,str) and COLOR.fullmatch(v) for v in (fill,stroke)):
            raise VectorArtError(f"Forma {n}: cor inválida")
        width=shape.get("w",4)
        if not isinstance(width,(int,float)) or not math.isfinite(width) or not 1<=width<=12:
            raise VectorArtError(f"Forma {n}: espessura inválida")
        items.append({"shape":shape["t"],"bbox":[x1,y1,x2,y2],
                      "fill":fill,"stroke":stroke,"width":width})
    return validate_art({"elements":items})

def local_instructions(actor,model="qwen2.5:7b",requester=None):
    label=(actor.get("visual_query_en") or actor.get("label_en") or
           actor.get("label") or actor.get("display_name") or actor.get("id") or "")
    if len(str(label))<3:raise VectorArtError("Personagem sem descrição")
    prompt=(
        "Crie uma ilustração vetorial 2D infantil ORIGINAL em fundo transparente. "
        "Somente um sujeito identificável, sem texto ou cenário: "+str(label)+". "
        "Use 8 a 14 elipses/retângulos, contorno escuro, cores vivas. "
        "Responda JSON compacto com e: lista de formas. "
        "Cada forma usa t=ellipse|rectangle, "
        "b=[x1,y1,x2,y2] para ellipse/rectangle, "
        
        "f=cor de preenchimento #RRGGBB, s=contorno #RRGGBB, w=largura. "
        "Coordenadas de 0 a 512. Monte corpo, rosto e detalhes em camadas. "
        "Não desenhe fundo. Categoria "+str(actor.get("kind","object"))+"."
    )
    if requester is None:
        def requester(payload):
            req=Request("http://127.0.0.1:11434/api/generate",
                        data=json.dumps(payload).encode("utf8"),
                        headers={"Content-Type":"application/json"})
            with urlopen(req,timeout=420) as reply:return json.load(reply)
    # Use strict required fields: the small Ollama model frequently invents
    # invalid optional polygon points or emits inverted boxes.
    item_schema={"type":"object","properties":{
       "t":{"type":"string","enum":["ellipse","rectangle"]},
       "b":{"type":"array","items":{"type":"integer"},"minItems":4,"maxItems":4},
       "f":{"type":"string","pattern":"^#[0-9a-fA-F]{6}$"},
       "s":{"type":"string","pattern":"^#[0-9a-fA-F]{6}$"},
       "w":{"type":"integer","minimum":1,"maximum":12}
    },"required":["t","b","f","s","w"],"additionalProperties":False}
    schema={"type":"object","properties":{
        "e":{"type":"array","items":item_schema,"minItems":8,"maxItems":14}},
        "required":["e"],"additionalProperties":False}
    payload={"model":model,"prompt":prompt,"format":schema,"stream":False,
             "options":{"temperature":.1,"num_predict":2200}}
    try:
        raw=requester(payload)
    except (OSError,KeyError,TypeError,ValueError) as exc:
        raise VectorArtError('Falha comunicando com Ollama: '+str(exc)) from exc
    try:
        data=json.loads(raw['response'])
    except (KeyError,TypeError,ValueError) as exc:
        preview=str(raw.get('response',''))[:160] if isinstance(raw,dict) else ''
        reason=str(raw.get('done_reason','?')) if isinstance(raw,dict) else '?'
        raise VectorArtError('JSON inválido; done_reason='+reason+'; início='+repr(preview)+'; erro='+str(exc)) from exc
    if isinstance(data,dict) and "e" in data:
        data=normalize_simple_shapes(data)
    validate_art(data)
    return data,prompt

def generate_actor(actor,output,model="qwen2.5:7b",requester=None):
    target=Path(output)
    if target.is_file() and target.stat().st_size>1000:
        with Image.open(target) as image:
            if image.mode=="RGBA" and image.getchannel("A").getextrema()[0]<255:
                return target
    data,prompt=local_instructions(actor,model,requester)
    image=rasterize(data,target)
    info={"source":"local-Ollama-drawing","model":model,"subject":actor.get("id"),
          "description":actor.get("visual_query_en") or actor.get("id"),
          "requires_artistic_review":True,
          "drawing_sha256":hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),
          "note":"Formas originais geradas por IA local; verificar semelhança, anatomia e fatos"}
    target.with_suffix(".json").write_text(json.dumps(info,ensure_ascii=False,indent=2),
                                          encoding="utf8")
    return image
