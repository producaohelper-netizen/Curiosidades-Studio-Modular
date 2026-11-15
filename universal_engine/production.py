"""Produção unificada, verificável e com falha explícita quando faltam assets.

Reúne: Trends -> Ollama -> SceneSpec -> Commons/OpenCLIP/ComfyUI -> Piper ->
camadas PNG transparentes -> FFmpeg -> relatório. Não promete qualidade
profissional por uma mera exportação; a aprovação artística é separada.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import json
import os
import shutil
import subprocess
import time
import re
import uuid
import unicodedata

from .trends import fetch_trends, top_five
from .storyboard_planner import plan_script
from .visual_pipeline import build_scene_asset, SceneAsset
from .vector_drawer import generate_actor
from .narration import generate_piper, retime_to_audio
from .layer_renderer import render_clip
from .scenespec import validate
from .sprite_factory import produce_sprite
from .photo_layers import extract_for_scene
from .illustrated_layers import has_alpha, alpha_sprite, create_background
from .foreground_match import verify_foreground
from .comfy_auto import auto_workflow, ComfySetupError


class ProductionError(RuntimeError):
    pass


@dataclass
class Settings:
    workspace: str
    voice_model: str
    piper: str = "piper"
    llm: str = "qwen2.5:7b"
    comfy_workflow: str | None = None
    fps: int = 24
    width: int = 1280
    height: int = 720
    topic: str | None = None
    approval_required: bool = True
    sprite_workflow: str | None = None
    auto_comfy: bool = True
    vector_fallback: bool = True


def atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf8")
    tmp.replace(path)


def choose_topic(settings: Settings):
    if settings.topic:
        return {"title": settings.topic, "source": "manual", "trending": False}
    try:
        trends = top_five(fetch_trends())
    except Exception as exc:
        raise ProductionError("Não foi possível obter tendências reais: " + str(exc)) from exc
    if not trends:
        raise ProductionError("Não há tendência apropriada para vídeo educativo")
    t = trends[0]
    return {"title": t["title"], "source": t["source"],
            "trending": True, "traffic_label": t["traffic_label"]}


def _ollama_json(prompt: str, model: str, timeout=900, requester=None):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "format": "json",
                          "options": {"temperature": .45, "num_predict": 4600}}).encode("utf8")
    request = Request("http://127.0.0.1:11434/api/generate", data=payload,
                      headers={"Content-Type": "application/json"})
    if requester is None:
        def requester(req, timeout):
            with urlopen(req, timeout=timeout) as response:
                return json.load(response)
    try:
        answer = requester(request, timeout)
        if answer.get("error"):
            raise ProductionError("Ollama: " + str(answer["error"]))
        return json.loads(answer["response"])
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise ProductionError("Ollama não respondeu com JSON válido: " + str(exc)) from exc


def write_story(topic, llm, generator=None):
    prompt = f"""Escreva UM roteiro ORIGINAL de curiosidade para YouTube em português
brasileiro, de aproximadamente cinco minutos, sobre {topic!r}.
Explique com exemplos concretos que uma criança entenda, 1 narrador, humor
inocente/situacional, sem copiar personagens famosos. Sem frases de enchimento,
sem inventar fatos científicos ou informações atuais não verificadas.
Resposta APENAS JSON no formato:
{{"title":"...","sections":[{{"text":"parágrafo contínuo de 100-125 palavras"}}]}}
EXATAMENTE 6 sections e cerca de 650-730 palavras no total. Cada parágrafo
deve permitir ilustrações de ações específicas, não imagens de preenchimento.
Não inclua instruções de animação dentro da fala.
"""
    result = generator(prompt) if generator else _ollama_json(prompt, llm)
    sections = result.get("sections") if isinstance(result, dict) else None
    if not isinstance(sections, list) or len(sections) != 6:
        raise ProductionError("Roteiro precisa de seis seções")
    for part in sections:
        if not isinstance(part, dict) or not isinstance(part.get("text"), str):
            raise ProductionError("Seção inválida")
    narration = "\n".join(part["text"].strip() for part in sections)
    words = len(narration.split())
    if not 610 <= words <= 760:
        raise ProductionError(f"Roteiro com {words} palavras; esperado 610–760")
    return {"title": str(result.get("title") or topic), "sections": sections,
            "narration": narration, "words": words}


def check_character_consistency(scenes):
    """One recurring actor ID must never turn into a different asset."""
    actors = {}
    assets = {}
    for scene in scenes:
        for actor in scene["actors"]:
            name = actor["id"].casefold().strip()
            kind = actor["kind"]
            asset = actor["asset_id"]
            if name in actors and actors[name] != (kind, asset):
                raise ProductionError(
                    f"Personagem recorrente '{name}' mudou kind/asset_id entre cenas"
                )
            if asset in assets and assets[asset] != kind:
                raise ProductionError(
                    f"asset_id '{asset}' reutilizado por tipos incompatíveis"
                )
            actors[name] = kind, asset
            assets[asset] = kind
    return {"recurring_ids": len(actors), "unique_assets": len(assets)}


def assert_preflight(settings):
    missing = []
    for item in ("ffmpeg", "ffprobe", settings.piper):
        if not (shutil.which(item) or Path(item).is_file()):
            missing.append(item)
    if not Path(settings.voice_model).is_file():
        missing.append("modelo Piper .onnx")
    if not Path(settings.voice_model + ".json").is_file():
        missing.append("configuração Piper .onnx.json")
    if missing:
        raise ProductionError("Dependências ausentes: " + ", ".join(missing))
    if settings.fps != 24 or settings.width < 960 or settings.height < 540:
        raise ProductionError("Exige 24 FPS e pelo menos 960×540")


def asset_path(base: Path, asset_id: str):
    # Untrusted strings from the model must not escape the asset directory.
    if not isinstance(asset_id, str) or not asset_id:
        raise ProductionError("asset_id inválido")
    digest = hashlib.sha256(asset_id.encode("utf8")).hexdigest()[:24]
    return base / (digest + ".png")


def prepare_scene_assets(scene, work: Path, settings: Settings, *,
                         get_asset=build_scene_asset):
    """Search/generate BACKGROUND; actors need RGBA assets with known IDs.

    There is deliberately NO automatic inference that a full Wikimedia
    photograph is a transparent character sprite.
    """
    scene_id = scene["scene_id"]
    result = get_asset(scene, work / "image_search",
                       comfy_workflow=settings.comfy_workflow)
    if not result.file:
        if not settings.vector_fallback:
            raise ProductionError(f"{scene_id}: falta imagem pertinente ao roteiro: {result.reason}")
        bg=work/"scene_backgrounds"/(scene_id+".png")
        create_background(scene.get("setting",{}).get("kind","nature"),bg,identity=scene_id)
        sprites={}
        try:
            for actor in scene["actors"]:
                dest=asset_path(work/"characters",actor["asset_id"])
                generate_actor(actor,dest,model=settings.llm)
                verify_foreground(actor,scene,dest,minimum=.16)
                sprites[actor["asset_id"]]=dest
        except Exception as exc:
            raise ProductionError(f"{scene_id}: ilustração vetorial inválida: {exc}") from exc
        asset=SceneAsset(scene_id,str(bg),"local-ollama-vector","",True,
                         "Desenho local por formas: revisão artística obrigatória",
                         scene.get("visual_query_en",""),"local-generated-unreviewed","", "",
                         scene.get("visual_style","cartoon"))
        return bg,sprites,asset
    if not result.license_name and result.source != "local-comfyui":
        raise ProductionError(f"{scene_id}: imagem sem licença rastreável")
    sprites = {}
    # In CPU-only mode, remove the photographed subject from EVERY backdrop,
    # even when the reusable sprite was cached by an earlier scene.
    if result.source=="Wikimedia Commons" and len(scene["actors"])==1 and not settings.sprite_workflow:
        actor=scene["actors"][0]
        dst=asset_path(work/"characters",actor["asset_id"])
        background=work/"scene_backgrounds"/(scene_id+".png")
        if not background.is_file():
            temporary=dst if not dst.is_file() else work/"scene_backgrounds"/(scene_id+"_discard.png")
            if scene.get('visual_style')=='cartoon' and has_alpha(result.file):
                if not dst.is_file():alpha_sprite(result.file,dst)
                temporary=dst
                create_background(scene.get('setting',{}).get('kind','nature'),background,identity=scene_id)
            else:
                extract_for_scene(scene,result.file,temporary,background)
                if scene.get('visual_style')=='cartoon':
                    create_background(scene.get('setting',{}).get('kind','nature'),background,identity=scene_id)
            try:
                verification=verify_foreground(actor,scene,temporary)
                result.reason += "; OpenCLIP do recorte: "+str(round(verification["score"],3))
            except Exception:
                background.unlink(missing_ok=True)
                if temporary!=dst:temporary.unlink(missing_ok=True)
                raise
            if temporary!=dst:temporary.unlink(missing_ok=True)
        result.file=str(background)
        result.reason += "; composição de camadas: revisão visual necessária"
        result.review_required=True
    for actor in scene["actors"]:
        dst=asset_path(work/"characters",actor["asset_id"])
        if not dst.is_file():
            if settings.sprite_workflow:
                produce_sprite(actor,work/"characters",settings.sprite_workflow)
            else:
                raise ProductionError(
                    f"{scene_id}: ator {actor['asset_id']} sem sprite RGBA "
                    "e sem extração confiável; configure ComfyUI"
                )
        from PIL import Image
        with Image.open(dst) as image:
            if image.mode!="RGBA" or image.getchannel("A").getextrema()[0]>=255:
                raise ProductionError(f"{scene_id}: sprite {dst.name} sem transparência")
        sprites[actor["asset_id"]]=dst
    return Path(result.file), sprites, result


def concatenate(clips: list[Path], output: Path, ffmpeg="ffmpeg"):
    """Join verified scene clips even when final MP4 is in a parent directory.

    FFmpeg concat-list paths are relative to the list file itself, not the
    final output. The old code erroneously required clips in output.parent.
    """
    clips=[Path(p) for p in clips]
    output=Path(output)
    if not clips or any(not p.is_file() or p.stat().st_size<1024 for p in clips):
        raise ProductionError("Lista de clipes vazia, incompleta ou inválida")
    sources={p.parent.resolve() for p in clips}
    if len(sources)!=1:
        raise ProductionError("Os clipes precisam estar na mesma pasta")
    clip_dir=clips[0].parent
    output.parent.mkdir(parents=True,exist_ok=True)
    concatfile=clip_dir/"lista_ffmpeg.txt"
    # Every video is generated by this app using clip_###.mp4 names.
    # Reject untrusted filenames rather than escaping arbitrary FFmpeg URLs.
    for p in clips:
        if not re.fullmatch(r"clip_[0-9]{3,5}\.mp4",p.name):
            raise ProductionError("Nome de clipe não é válido: "+p.name)
    concatfile.write_text(
        "".join("file '"+p.name+"'\n" for p in clips),encoding="utf8")
    cmd=[ffmpeg,"-hide_banner","-loglevel","error","-y",
         "-f","concat","-safe","0","-i",str(concatfile),
         "-c","copy","-movflags","+faststart",str(output)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode or not output.is_file() or output.stat().st_size<1024:
        raise ProductionError("FFmpeg não reuniu os vídeos: "+result.stderr[-1000:])
    return output


def probe_duration(video):
    output = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)], text=True)
    return float(output.strip())


def run(settings: Settings, *, story_writer=write_story,
        planner=plan_script, asset_provider=build_scene_asset,
        tts=generate_piper, clip_renderer=render_clip,
        topic_selector=choose_topic, mux=concatenate, probe=probe_duration):
    assert_preflight(settings)
    workspace=Path(settings.workspace)
    workspace.mkdir(parents=True,exist_ok=True)
    topic=topic_selector(settings)
    title=str(topic.get("title","curiosidade"))
    normalized=unicodedata.normalize("NFKD",title)
    slug=re.sub(r"[^a-z0-9]+","-",normalized.encode("ascii","ignore").decode("ascii").lower())
    slug=slug.strip("-")[:44] or "curiosidade"
    episode_id=time.strftime("%Y%m%d_%H%M%S")+"_"+slug+"_"+uuid.uuid4().hex[:6]
    root=workspace/"episodes"/episode_id
    root.mkdir(parents=True,exist_ok=False)
    status_path=root/"status.json"
    report={"status":"started","stages":[],"issues":[],
            "artistic_approval":"NOT_PERFORMED",
            "workspace":str(root),"topic":topic}
    atomic_json(workspace/"ultimo_episodio.json",
                {"workspace":str(root),"episode_id":episode_id,"topic":topic})
    def stage(name, **extras):
        report["stages"].append({"stage": name, "at": time.time(), **extras})
        atomic_json(status_path, report)
        print(name, flush=True)
    try:
        stage("topic", topic=topic)
        story = story_writer(topic["title"], settings.llm)
        atomic_json(root/"roteiro.json", story)
        stage("script", words=story["words"])
        # Detect the art engine BEFORE planning. CPU/photo fallback can only
        # isolate one reliable actor per scene.
        if settings.auto_comfy and (not settings.comfy_workflow or not settings.sprite_workflow):
            try:
                chosen=auto_workflow(root/"model_comfy_api.json")
                settings.comfy_workflow=settings.comfy_workflow or chosen["workflow"]
                settings.sprite_workflow=settings.sprite_workflow or chosen["workflow"]
                stage("comfy_checkpoint_detected", checkpoint=chosen["checkpoint"])
            except Exception as exc:
                stage("comfy_unavailable", note=str(exc)[:220],
                      fallback="licensed-photos + rembg for one-actor scenes")
        if planner is plan_script:
            storyboard = planner(story["narration"], max_words=15,
                                 max_actors=4 if settings.sprite_workflow else 1)
        else:
            storyboard = planner(story["narration"], max_words=15)
        scenes = storyboard["scenes"]
        if not 40 <= len(scenes) <= 100:
            raise ProductionError("Storyboard precisa de 40–100 cenas; "
                                  f"recebeu {len(scenes)}")
        for scene in scenes:
            validate(scene)
            # Explicit product requirement: illustrations rather than documentary
            # photographs, unless a future project explicitly chooses a hybrid.
            scene.setdefault("visual_style","cartoon")
        identity=check_character_consistency(scenes)
        atomic_json(root/"storyboard.json", storyboard)
        stage("visual_plan", scenes=len(scenes), **identity)
        clips = []
        sound_total = 0.
        asset_log = []
        for index, scene in enumerate(scenes):
            scene_dir = root/"shots"/f"{index:03}"
            scene_dir.mkdir(parents=True, exist_ok=True)
            bg, sprites, asset = prepare_scene_assets(
                scene, root/"assets", settings, get_asset=asset_provider)
            asset_log.append(asdict(asset))
            voice = tts(scene["narration"], settings.voice_model,
                        scene_dir/"speech.wav", executable=settings.piper)
            sound_total += voice["duration"]
            aligned = retime_to_audio(scene, voice["duration"])
            clip = root/"clips"/f"clip_{index:03}.mp4"
            clip.parent.mkdir(parents=True, exist_ok=True)
            clip_renderer(aligned, bg, sprites, voice["path"], clip,
                          fps=settings.fps, size=(settings.width, settings.height))
            clips.append(clip)
            if index % 5 == 0 or index == len(scenes)-1:
                stage("scene_render", index=index+1, total=len(scenes),
                      narration_seconds=round(sound_total,2))
        atomic_json(root/"licencas_e_assets.json", asset_log)
        # Créditos rastreáveis; não substitui a revisão das condições CC BY-SA.
        credits=[]
        seen=set()
        for item in asset_log:
            source=item.get("original_url") or item.get("file")
            if not source or source in seen:
                continue
            seen.add(source)
            credits.append(
                "Fonte: "+str(item.get("source",""))+"\n"+
                "Autor/crédito: "+str(item.get("attribution",""))+"\n"+
                "Licença: "+str(item.get("license_name",""))+"\n"+
                "Link: "+str(item.get("original_url",""))+"\n"
            )
        (root/"creditos_para_descricao_youtube.txt").write_text(
            "CRÉDITOS DE IMAGENS — verificar licenças antes de publicar\n\n"+
            "\n".join(credits),encoding="utf8")
        if not 285 <= sound_total <= 315:
            raise ProductionError(f"Narração total {sound_total:.1f}s fora de 5 minutos; "
                                  "não acelerar nem cortar artificialmente")
        stage("audio_duration_checked", seconds=round(sound_total,2))
        video = mux(clips, root/"video_provisorio.mp4")
        final_length = probe(video)
        if not 285 <= final_length <= 315:
            raise ProductionError(f"MP4 tem {final_length:.1f}s; duração fora da meta")
        report["status"] = "rendered_pending_editorial_review"
        report["output"] = str(video)
        report["duration"] = final_length
        stage("finished_pending_review", duration=round(final_length,2))
        return report
    except Exception as exc:
        report["status"] = "failed"
        report["issues"].append(f"{type(exc).__name__}: {exc}")
        atomic_json(status_path, report)
        raise


def cli():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--voice-model", required=True)
    ap.add_argument("--piper", default="piper")
    ap.add_argument("--llm", default="qwen2.5:7b")
    ap.add_argument("--comfy-workflow")
    ap.add_argument("--sprite-workflow")
    ap.add_argument("--disable-auto-comfy",action="store_true")
    ap.add_argument("--topic")
    ap.add_argument("--quality", choices=["720", "1080"], default="720")
    args = ap.parse_args()
    width, height = (1920,1080) if args.quality == "1080" else (1280,720)
    settings = Settings(args.workspace,args.voice_model,args.piper,args.llm,
                        args.comfy_workflow,24,width,height,args.topic,
                        sprite_workflow=args.sprite_workflow,
                        auto_comfy=not args.disable_auto_comfy)
    try:
        run(settings)
    except Exception as exc:
        print("PRODUÇÃO NÃO APROVADA:", exc, flush=True)
        raise SystemExit(2)


if __name__ == "__main__":
    cli()
