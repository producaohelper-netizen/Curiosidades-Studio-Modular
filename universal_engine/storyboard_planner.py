"""Transforma roteiro em SceneSpecs genéricos com IA local Ollama.

A IA não reescreve falas: só propõe direção artística.
Os testes podem fornecer um gerador simulado; produção usa o Ollama real.
"""
from __future__ import annotations
import json,re,hashlib,time
from urllib.request import Request,urlopen
from .scenespec import ACTIONS, KINDS, validate, SceneError

class PlanningError(RuntimeError):
    pass

def split_narration(text:str, max_words=23)->list[str]:
    if not isinstance(text,str) or not text.strip():
        raise PlanningError("Roteiro vazio")
    # Preserve punctuation and words; normalize whitespace only.
    raw=re.sub(r"\s+"," ",text.strip())
    sentences=re.split(r"(?<=[.!?])\s+(?=[A-ZÁÂÃÉÊÍÓÔÕÚÇ0-9])",raw)
    chunks=[]
    for sentence in sentences:
        words=sentence.split()
        while len(words)>max_words:
            chunks.append(" ".join(words[:max_words]))
            words=words[max_words:]
        if words:chunks.append(" ".join(words))
    return chunks

def _read_ollama(prompt:str, url="http://127.0.0.1:11434/api/generate",
                 model="qwen2.5:7b", timeout=180):
    if url not in ("http://127.0.0.1:11434/api/generate",
                   "http://localhost:11434/api/generate"):
        raise PlanningError("Ollama deve ser local")
    payload={"model":model,"prompt":prompt,"format":"json","stream":False,
             "options":{"temperature":.2,"num_predict":1800}}
    req=Request(url,data=json.dumps(payload).encode("utf8"),
                headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=timeout) as response:
        result=json.load(response)
    if result.get("error"):
        raise PlanningError("Ollama retornou erro: "+str(result["error"]))
    try:
        return json.loads(result["response"])
    except (KeyError,ValueError,TypeError) as err:
        raise PlanningError("Ollama retornou JSON inválido") from err

def plan_batch(narrations:list[str], start_index:int=0, generator=None,
               known_actors:dict|None=None)->list[dict]:
    if not narrations or len(narrations)>5:raise PlanningError("Lote deve ter 1 a 5 falas")
    context=json.dumps([{"index":start_index+i,"narration":line}
                        for i,line in enumerate(narrations)],ensure_ascii=False)
    known_actors=known_actors if known_actors is not None else {}
    registry=json.dumps(known_actors,ensure_ascii=False)
    prompt=f"""Você é diretor de animação infantil educativa em português.
Transforme as falas abaixo em um JSON com campo "scenes" (array do mesmo comprimento,
mesma ordem), sem inventar fatos científicos.
Cada cena precisa de:
- "visual_query_en": descrição visual EM INGLÊS (20-40 palavras) do que se vê;
- "search_terms_en": STRING contendo 2-5 palavras-chave EM INGLÊS para Wikimedia Commons;
- "setting": objeto com campo "kind" ("space","underwater","workshop","forest", etc.);
- "visual_fact": afirmação factual que a ilustração representa;
- "callout": 1 a 4 palavras presentes na fala, para rótulo discreto na tela;
- "actors": array de 1-4 objetos {{id,kind,asset_id,x,y}},
  kind em {sorted(KINDS)}. Mesmo elemento recorrente conserva asset_id entre cenas.
  IDENTIDADES DE LOTES ANTERIORES: {registry}
  Reutilize o mesmo asset_id para atores com o mesmo id.
- "timeline": array ordenado cronologicamente de 2-5 ações.
Cada ação tem at (segundos a partir de zero), action em {sorted(ACTIONS)},
target = id de ator existente, e outros campos necessários (to_x, to_y,
duration, towards, effect, emotion). Distribua ações dentro de no máximo 7 segundos.
Enquadramentos claros, expressões, humor visual leve, nunca imagens decorativas.
SEM texto explicativo ao redor; apenas JSON.
Falas (não altere nem reescreva; serão inseridas pelo programa):
{context}"""
    output=(generator or _read_ollama)(prompt)
    scenes=output.get("scenes") if isinstance(output,dict) else None
    if not isinstance(scenes,list) or len(scenes)!=len(narrations):
        raise PlanningError("Ollama não retornou uma cena por fala")
    done=[]
    for offset,(line,raw) in enumerate(zip(narrations,scenes)):
        if not isinstance(raw,dict):raise PlanningError("Cena não é objeto JSON")
        expected_seconds=max(2.0,min(55.0,round(len(line.split())/2.5,2)))
        scene={"version":1,
               "scene_id":f"scene_{start_index+offset:03}",
               "narration":line,
               "duration_target_seconds":expected_seconds,
               "setting":raw.get("setting",{}),
               "actors":raw.get("actors",[]),
               "timeline":raw.get("timeline",[]),
               "visual_fact":raw.get("visual_fact",""),
               "callout":raw.get("callout",""),
               "visual_query_en":raw.get("visual_query_en",""),
               "search_terms_en":raw.get("search_terms_en","")}
        if len(scene["visual_query_en"].strip())<12:
            raise PlanningError("Cena sem descrição visual suficiente")
        if not isinstance(scene["search_terms_en"],str) or not scene["search_terms_en"].strip():
            raise PlanningError("Cena sem palavras-chave para banco de imagens")
        for actor in scene["actors"]:
            ident=actor["id"].casefold().strip()
            previous=known_actors.get(ident)
            if previous:
                if actor["kind"]!=previous["kind"]:
                    raise PlanningError(f"Ator {ident} mudou de tipo entre cenas")
                actor["asset_id"]=previous["asset_id"]
            else:
                known_actors[ident]={"kind":actor["kind"],
                                     "asset_id":actor["asset_id"]}
        try:validate(scene)
        except SceneError as err:raise PlanningError(f"SceneSpec inválido: {err}") from err
        done.append(scene)
    return done

def plan_script(script:str, generator=None, max_words=23):
    lines=split_narration(script,max_words)
    scenes=[]
    registry={}
    for i in range(0,len(lines),5):
        scenes.extend(plan_batch(lines[i:i+5],i,generator,registry))
    return {"schema_version":1,"scenes":scenes,
            "estimated_duration":round(sum(x["duration_target_seconds"] for x in scenes),1),
            "requires_real_audio_timing":True}
