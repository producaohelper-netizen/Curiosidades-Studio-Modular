"""Gate técnico-editorial mínimo; não substitui avaliação humana."""
import argparse,json,subprocess,pathlib
def inspect(video,story):
    meta=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",video],text=True))
    streams=meta["streams"]
    v=next((x for x in streams if x["codec_type"]=="video"),{})
    a=next((x for x in streams if x["codec_type"]=="audio"),{})
    duration=float(meta["format"].get("duration",0))
    data=json.loads(pathlib.Path(story).read_text(encoding="utf-8"))
    beats=sum(len(x.get("visual_labels",[])) for x in data.get("scenes",[]))
    actions=sum(len(x.get("visual_actions",[])) for x in data.get("scenes",[]))
    checks={
      "five_minutes":285<=duration<=315,
      "full_hd":v.get("width",0)>=1920 and v.get("height",0)>=1080,
      "video_h264":v.get("codec_name")=="h264",
      "audio_aac":a.get("codec_name")=="aac",
      "at_least_45_visual_beats":beats>=45,
      "under_8_seconds_per_beat":beats>0 and duration/beats<=8,
      "actions_per_chapter":actions>=len(data.get("scenes",[]))*4
    }
    checks["complete_decode"]=subprocess.run(["ffmpeg","-v","error","-xerror","-i",video,"-f","null","-"],capture_output=True).returncode==0
    return {"passed":all(checks.values()),"checks":checks,"duration_seconds":duration,"planned_beats":beats,"explicit_actions":actions,"artistic_approval":"requires human review"}
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("video");ap.add_argument("story");args=ap.parse_args()
    result=inspect(args.video,args.story);print(json.dumps(result,indent=2,ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 2)
