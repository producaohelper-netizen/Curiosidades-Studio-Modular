"""Licensed multi-actor 2D composition, without a dedicated image GPU.

An actor is searched by its OWN visual description. Its PNG and provenance are
cached by asset_id and reused across every scene in the episode. Missing or
opaque images are never accepted as transparent cartoon actors.
"""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from .illustrated_layers import alpha_sprite, create_background, has_alpha
from .visual_pipeline import SceneAsset, build_scene_asset


class MultiActorError(RuntimeError):
    pass


def _key(asset_id):
    if not isinstance(asset_id,str) or not asset_id.strip():
        raise MultiActorError("Identificador de personagem vazio")
    return hashlib.sha256(asset_id.encode("utf8")).hexdigest()[:24]


def illustrated_actors(scene, work, *, provider=build_scene_asset,
                       sprite_generator=None, sprite_workflow=None):
    actors=scene.get("actors",[])
    if len(actors)<2:
        raise MultiActorError("Este compositor exige ao menos dois atores")
    work=Path(work)
    sprites={}
    manifests=[]
    for actor in actors:
        key=_key(actor["asset_id"])
        png=work/"characters"/(key+".png")
        info=work/"characters"/(key+".json")
        if png.is_file():
            if not has_alpha(png) or not info.is_file():
                raise MultiActorError(
                    "Sprite em cache não é transparente ou não tem crédito: "+key)
            credit=json.loads(info.read_text(encoding="utf8"))
        else:
            label=(actor.get("visual_query_en") or actor.get("display_name") or
                   actor.get("id") or "")
            if len(str(label).strip())<5:
                raise MultiActorError("Ator sem descrição visual suficiente: "+key)
            actor_scene={"scene_id":"actor-"+key,"visual_style":"cartoon",
                         "visual_query_en":str(label),
                         "search_terms_en":str(actor.get("search_terms_en") or label)}
            result=provider(actor_scene,work/"search"/key,
                            comfy_workflow=None)
            if result.file and has_alpha(result.file):
                if not result.license_name:
                    raise MultiActorError("Falta licença para ilustração: "+key)
                alpha_sprite(result.file,png)
                credit={"asset_id":actor["asset_id"],
                        "source":result.source,"original_url":result.original_url,
                        "license_name":result.license_name,
                        "license_url":result.license_url,
                        "attribution":result.attribution,
                        "requires_visual_review":True}
            elif sprite_workflow and sprite_generator:
                sprite_generator(actor,work/"characters",sprite_workflow)
                if not png.is_file() or not has_alpha(png):
                    raise MultiActorError("Gerador não devolveu PNG RGBA: "+key)
                credit={"asset_id":actor["asset_id"],"source":"local-comfyui",
                        "original_url":"","license_name":"CHECK_MODEL_LICENSE",
                        "license_url":"","attribution":"local model",
                        "requires_visual_review":True}
            else:
                raise MultiActorError(
                    f"{actor['asset_id']}: nenhuma ilustração transparente compatível; "
                    "não substituir por foto nem personagem diferente")
            info.parent.mkdir(parents=True,exist_ok=True)
            info.write_text(json.dumps(credit,ensure_ascii=False,indent=2),
                            encoding="utf8")
        sprites[actor["asset_id"]]=png
        manifests.append(credit)
    background=work/"scene_backgrounds"/(scene["scene_id"]+".png")
    if not background.exists():
        create_background(scene.get("setting",{}).get("kind","nature"),
                          background,identity=scene["scene_id"])
    credits=work/"scene_backgrounds"/(scene["scene_id"]+"_credits.json")
    credits.write_text(json.dumps(manifests,ensure_ascii=False,indent=2),
                       encoding="utf8")
    summary=SceneAsset(scene["scene_id"],str(background),"illustrated-multi-actor",
                       "see per-actor manifests",True,
                       "Cada ator possui licença e origem individual no JSON de créditos",
                       scene.get("visual_query_en",""),
                       "SEE_PER_ACTOR_CREDITS","",str(credits),"cartoon")
    return background,sprites,summary
