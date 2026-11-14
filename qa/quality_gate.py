"""Controle técnico e de coerência visual; não determina qualidade artística sozinho."""
import argparse,json,subprocess,pathlib
def inspect(video,story):
    meta=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",video],text=True))
    streams=meta["streams"]
    v=next((x for x in streams if x["codec_type"]=="video"),{})
    a=next((x for x in streams if x["codec_type"]=="audio"),{})
    duration=float(meta["format"].get("duration",0))
    data=json.loads(pathlib.Path(story).read_text(encoding="utf-8"))
    scenes=data.get("scenes",[])
    beats=sum(len(x.get("visual_labels",[])) for x in scenes)
    actions=sum(len(x.get("visual_actions",[])) for x in scenes)
    # New SceneSpecs, when available, are the authoritative visual plan.
    specs=[x for x in scenes if x.get("version")==1]
    action_names={"move","approach","escape","react","emit_particles","follow",
                  "orbit","pulse","reveal","enter","exit","compare"}
    semantic_actions=sum(sum(step.get("action") in action_names for step in s.get("timeline",[]))
                         for s in specs)
    planned=len(specs)==len(scenes) and len(scenes)>=20 and all(
        len(s.get("visual_query_en","").strip())>=12 and
        bool(s.get("visual_fact","").strip()) and
        len(s.get("timeline",[]))>=2 for s in specs
    )
    checks={
      "five_minutes":285<=duration<=315,
      "full_hd":v.get("width",0)>=1920 and v.get("height",0)>=1080,
      "video_h264":v.get("codec_name")=="h264",
      "audio_aac":a.get("codec_name")=="aac",
      "all_scenes_have_visual_plan":planned,
      "non_decorative_actions":semantic_actions>=len(specs) if specs else False
    }
    checks["complete_decode"]=subprocess.run(["ffmpeg","-v","error","-xerror","-i",video,"-f","null","-"],capture_output=True).returncode==0
    # Cuts/changes are diagnostic, not proof of quality: the rejected
    # prior video changed images more often than the reference.
    return {"passed":all(checks.values()),"checks":checks,
            "duration_seconds":duration,"legacy_visual_beats":beats,
            "legacy_visual_actions":actions,"semantic_actions":semantic_actions,
            "artistic_approval":"requires side-by-side review with user reference"}
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("video");ap.add_argument("story");args=ap.parse_args()
    result=inspect(args.video,args.story);print(json.dumps(result,indent=2,ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 2)
