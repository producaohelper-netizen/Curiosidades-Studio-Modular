"""Google Trends Brasil RSS: consulta real + shortlist editorial transparente.

O RSS retorna tendências recentes (não um ranking completo do país).
Não cria tópicos quando a rede falha. Evita notícias incompatíveis com humor
infantil e prioriza perguntas explicáveis visualmente.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from urllib.request import Request,urlopen
from xml.etree import ElementTree as ET
import re, json
from pathlib import Path

RSS_URL="https://trends.google.com/trending/rss?geo=BR"
HT="{https://trends.google.com/trending/rss}"
FACTUAL_DOMAINS={
 "el niño":3,"eclipse":3,"meteoro":3,"planeta":3,"astronomia":3,
 "tempestade solar":3,"vulcão":3,"ciclone":2,"ia":1,
 "inteligência artificial":2,"dinossauro":3,"oceano":3,"animal":3,
 "nasa":3,"energia":2,"robô":2,"robôs":2,"foguete":3,"lua":3,
}
CAUTION_TERMS=(
 "assassinato","morte","acidente fatal","tragédia","massacre",
 "presidente","eleição","pronunciamento","crime","guerra","atentado",
 "delegado","cnj","polícia","preso","banco master",
)
MATCH_TERMS=(" x "," vs ","classificação","placar","gabarito","resultado","apostas","loteria")

@dataclass(frozen=True)
class Trend:
    title:str
    traffic_label:str
    traffic_estimate:int
    published:str
    source:str="Google Trends RSS Brazil"

def traffic(label:str)->int:
    t=label.strip().lower().replace(",","")
    m=re.search(r"(\d+(?:\.\d+)?)\s*([kmb])?",t)
    if not m:return 0
    multiplier={"k":1000,"m":1000000,"b":1000000000}.get(m.group(2),1)
    return int(float(m.group(1))*multiplier)

def parse_rss(xml_bytes:bytes)->list[Trend]:
    root=ET.fromstring(xml_bytes)
    out=[]
    for item in root.findall("./channel/item"):
        title=(item.findtext("title") or "").strip()
        volume=(item.findtext(HT+"approx_traffic") or "").strip()
        if title:
            out.append(Trend(title,volume,traffic(volume),
                             (item.findtext("pubDate") or "").strip()))
    return out

def fetch_trends(timeout:int=18)->list[Trend]:
    req=Request(RSS_URL,headers={"User-Agent":"Mozilla/5.0 CuriosidadesStudio/1.0"})
    with urlopen(req,timeout=timeout) as response:
        return parse_rss(response.read(2_000_000))

def suitability(t:Trend)->tuple[int,list[str]]:
    name=t.title.casefold()
    reasons=[]
    if any(bad in name for bad in CAUTION_TERMS):
        return -999,["Tema inadequado para humor infantil; revisão editorial"]
    penalty=12 if any(bad in name for bad in MATCH_TERMS) else 0
    relevant=0
    for term,points in FACTUAL_DOMAINS.items():
        if term in name:relevant=max(relevant,points)
    score=int(min(25,t.traffic_estimate**.22 if t.traffic_estimate else 0))
    score+=relevant*12-penalty
    if relevant:reasons.append("potencial educativo e visual")
    if penalty:reasons.append("tendência de resultado esportivo; evitar simples placar")
    reasons.append("volume aproximado do RSS")
    return score,reasons

def top_five(trends:list[Trend])->list[dict]:
    ranked=[]
    for t in trends:
        score,reason=suitability(t)
        if score<=-100:continue
        ranked.append({**asdict(t),"editorial_score":score,"notes":reason})
    ranked.sort(key=lambda x:(x["editorial_score"],x["traffic_estimate"]),reverse=True)
    return ranked[:5]

def save_results(items:list[dict],path:str|Path):
    file=Path(path);file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps({"source":RSS_URL,"trends":items,
                                "ranking_scope":"recent RSS results, not all Brazilian Google searches",
                                "human_review_required":True},ensure_ascii=False,indent=2),encoding="utf8")
    return file
