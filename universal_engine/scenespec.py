"""Motor universal 2D: SceneSpec versionado, validacao e interpolacao de acoes.

Atores genericos e cenarios abstratos permitem testar composicao em multiplos
assuntos sem depender de um desenho unico. Artistas/modelos podem fornecer
assets reais futuramente. Nenhuma qualidade artistica e presumida.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

ACTIONS = {
    "enter", "exit", "move", "approach", "escape", "rotate", "scale",
    "react", "highlight", "reveal", "compare", "emit_particles",
    "camera_push", "camera_pan", "pulse", "orbit", "follow",
}
KINDS = {"person", "animal", "object", "planet", "organ", "machine", "building", "label"}
SCHEMA_VERSION = 1

class SceneError(ValueError):
    pass

def validate(scene: dict) -> dict:
    """Validate references and timeline without silently inventing assets."""
    if not isinstance(scene, dict) or scene.get("version") != SCHEMA_VERSION:
        raise SceneError("SceneSpec precisa de version=1")
    if not isinstance(scene.get("scene_id"), str) or not scene["scene_id"].strip():
        raise SceneError("scene_id ausente")
    if not isinstance(scene.get("narration"), str) or not scene["narration"].strip():
        raise SceneError("narration ausente")
    duration = scene.get("duration_target_seconds")
    if not isinstance(duration, (int, float)) or not 1 <= duration <= 60 or not math.isfinite(duration):
        raise SceneError("duracao invalida: esperado 1 a 60 segundos")
    actors = scene.get("actors")
    if not isinstance(actors, list) or not actors or len(actors) > 16:
        raise SceneError("actors deve conter entre 1 e 16 elementos")
    ids = []
    for actor in actors:
        if not isinstance(actor, dict) or not isinstance(actor.get("id"), str):
            raise SceneError("actor invalido")
        if actor.get("kind") not in KINDS:
            raise SceneError("kind nao suportado")
        if not isinstance(actor.get("asset_id"), str) or not actor["asset_id"]:
            raise SceneError("asset_id obrigatorio para identidade visual")
        if not all(isinstance(actor.get(c, 0.5), (float, int)) and 0 <= actor.get(c, 0.5) <= 1 for c in ("x", "y")):
            raise SceneError("posicao de ator fora de 0..1")
        ids.append(actor["id"])
    if len(set(ids)) != len(ids):
        raise SceneError("id de ator duplicado")
    timeline = scene.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        raise SceneError("timeline vazia")
    last_time = -1
    for step in timeline:
        if not isinstance(step, dict) or step.get("action") not in ACTIONS:
            raise SceneError("acao ausente ou desconhecida")
        at = step.get("at")
        if not isinstance(at, (int, float)) or not math.isfinite(at) or not (0 <= at < duration):
            raise SceneError("tempo fora da cena")
        if at < last_time:
            raise SceneError("timeline fora de ordem")
        last_time = at
        target = step.get("target")
        if step["action"] not in ("camera_pan",) and target not in ids:
            raise SceneError(f"ator desconhecido: {target}")
        if step["action"] in ("move", "enter", "exit", "escape", "approach", "follow", "orbit"):
            if step.get("action") == "approach" and step.get("towards") not in ids:
                raise SceneError("approach exige towards valido")
            if step.get("action") in ("follow", "orbit") and step.get("towards") not in ids:
                raise SceneError("follow exige towards valido")
        if "duration" in step and (not isinstance(step["duration"], (int, float)) or
                                   step["duration"] <= 0 or at + step["duration"] > duration + 0.001):
            raise SceneError("duracao de acao invalida")
    if not isinstance(scene.get("visual_fact"), str) or not scene["visual_fact"].strip():
        raise SceneError("visual_fact obrigatorio para revisao de coerencia")
    return scene

def fingerprint(scene: dict) -> str:
    validate(scene)
    return hashlib.sha256(json.dumps(scene, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()

def motion(scene: dict, at: float) -> dict:
    """Pure function; returns actor transforms at a time in seconds.

    Positions use normalized coordinates. Animations interpolate against
    per-actor state. No frames need be regenerated when narration is unchanged.
    """
    validate(scene)
    state = {a["id"]: {"x": float(a.get("x", .5)), "y": float(a.get("y", .5)),
                       "scale": float(a.get("scale", 1.0)), "angle": 0.0,
                       "emotion": "neutral", "opacity": 1.0,
                       "effect": None, "highlight": False} for a in scene["actors"]}
    moves = {"move", "escape", "enter", "exit", "approach", "follow", "orbit"}
    timeline=scene["timeline"]
    for i, step in enumerate(timeline):
        start = float(step["at"])
        if at < start: break
        action = step["action"]
        target = step.get("target")
        duration = float(step.get("duration", .6))
        # Position actions interrupted by a subsequent movement start at the
        # *previous evaluated pose*, not the original actor position. This
        # avoids the visible teleporting observed in concatenated actions.
        cutoff=at
        if action in moves:
            for subsequent in timeline[i+1:]:
                if subsequent.get("target")==target and subsequent["action"] in moves:
                    cutoff=min(cutoff,float(subsequent["at"]))
                    break
        p = min(1.0, max(0.0, ((cutoff if action in moves else at)-start)/duration))
        ease = p*p*(3-2*p)
        if action in ("camera_pan","camera_push"): continue
        s = state[target]
        if action in ("move","escape","enter","exit","approach","follow"):
            sx,sy=s["x"],s["y"]
            dx=float(step.get("to_x",sx))
            dy=float(step.get("to_y",sy))
            if action in ("approach","follow"):
                other=state[step["towards"]]
                dx,dy=other["x"]-.12,other["y"]
            if action=="escape" and "to_x" not in step:
                dx=.06 if sx<.5 else .94
            s["x"]=sx+(dx-sx)*ease
            s["y"]=sy+(dy-sy)*ease
            if action=="enter":s["opacity"]=ease
            elif action=="exit":s["opacity"]=1-ease
        elif action=="orbit":
            focus=state[step["towards"]]
            sx,sy=s["x"]-focus["x"],s["y"]-focus["y"]
            radius=max(.04,math.hypot(sx,sy))
            initial=math.atan2(sy,sx)
            radians=math.radians(float(step.get("degrees",360)))*ease
            s["x"]=focus["x"]+radius*math.cos(initial+radians)
            s["y"]=focus["y"]+radius*math.sin(initial+radians)
        elif action=="rotate":
            s["angle"]=float(step.get("degrees",360))*ease
        elif action in ("scale","pulse"):
            size=float(step.get("factor",1.2))
            s["scale"]=1+(size-1)*(math.sin(p*math.pi) if action=="pulse" else ease)
        elif action=="react":
            s["emotion"]=str(step.get("emotion","surprised"))
        elif action=="highlight":
            s["highlight"]=True
        elif action in ("emit_particles","reveal"):
            s["effect"]=str(step.get("effect","sparkles"))
            s["effect_elapsed"]=max(0.,at-start)
    return state

def load(path: str | Path) -> dict:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))
