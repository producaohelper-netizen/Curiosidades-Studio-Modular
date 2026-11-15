"""Auditoria de vídeo renderizado: problemas objetivos não equivalem a aprovação artística."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path


def run_ffmpeg(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return {"returncode": p.returncode, "log": p.stderr[-12000:]}


def parse_ranges(log, start_key, end_key):
    starts = [float(x) for x in re.findall(rf"{re.escape(start_key)}:\s*([0-9.]+)", log)]
    ends = [float(x) for x in re.findall(rf"{re.escape(end_key)}:\s*([0-9.]+)", log)]
    return [{"start": round(a, 3), "end": round(b, 3), "seconds": round(b-a, 3)}
            for a, b in zip(starts, ends) if b >= a]


def audit(video, *, min_duration=285, max_duration=315):
    video = Path(video)
    if not video.is_file():
        raise FileNotFoundError(video)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video)],
        capture_output=True, text=True, check=True)
    meta = json.loads(probe.stdout)
    streams = meta.get("streams", [])
    visual = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    duration = float(meta.get("format", {}).get("duration", 0))
    # detect long black frames and extended audio silence; thresholds are diagnostic.
    black = run_ffmpeg(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(video),
                        "-vf", "blackdetect=d=1.0:pix_th=0.10", "-an", "-f", "null", "-"])
    silence = run_ffmpeg(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(video),
                          "-af", "silencedetect=noise=-40dB:d=2", "-vn", "-f", "null", "-"])
    black_ranges = parse_ranges(black["log"], "black_start", "black_end")
    silence_ranges = parse_ranges(silence["log"], "silence_start", "silence_end")
    # Silence at the beginning or end may be intentional. Report, do not auto-reject.
    checks = {
        "duration": min_duration <= duration <= max_duration,
        "full_hd": visual.get("width", 0) >= 1920 and visual.get("height", 0) >= 1080,
        "fps_24": visual.get("avg_frame_rate") in ("24/1", "48/2"),
        "h264": visual.get("codec_name") == "h264",
        "aac": audio.get("codec_name") == "aac",
        "black_scan_completed": black["returncode"] == 0,
        "silence_scan_completed": silence["returncode"] == 0,
        "no_long_black_frames": not black_ranges,
    }
    return {
        "video": str(video), "duration_seconds": duration,
        "checks": checks, "technical_passed": all(checks.values()),
        "black_intervals": black_ranges, "silence_intervals": silence_ranges,
        "audio_review_required": bool(silence_ranges),
        "artistic_approval": "PENDING_HUMAN_REFERENCE_COMPARISON",
        "notes": "Silence is diagnostic; no automatic claim of voice quality or artistic approval."
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--output", default=None)
    args = p.parse_args()
    result = audit(args.video)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["technical_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
