"""Render a first review-only vertical Reel from four user-approved images.

No unrelated stock images are invented. The caller supplies the exact visual
for each narrated section. This is an intermediate renderer, not an automated
fact-checker or a finished monetization-ready editor.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from pathlib import Path
from PIL import Image
from .reel_captions import caption_frame
from .reel_caption_timing import validate_cues
from .reel_visual_beats import reframe


class ReelRenderError(RuntimeError):
    pass


def render_reel(audio_path, cues, images, output, *, fps=24, size=(1080, 1920),
                ffmpeg="ffmpeg"):
    if len(images) != len(cues) or not images:
        raise ReelRenderError("É necessária uma imagem por trecho narrado")
    if size[0] >= size[1] or fps < 12 or fps > 30:
        raise ReelRenderError("Formato vertical ou FPS inválido")
    import wave
    with wave.open(str(audio_path), "rb") as wav:
        duration = wav.getnframes() / wav.getframerate()
    validate_cues(cues, duration)
    backgrounds = []
    try:
        for image_path in images:
            with Image.open(image_path) as original:
                image = original.convert("RGB")
                factor = max(size[0] / image.width, size[1] / image.height)
                scaled = image.resize((math.ceil(image.width * factor),
                                       math.ceil(image.height * factor)), Image.Resampling.LANCZOS)
                left = (scaled.width - size[0]) // 2
                top = (scaled.height - size[1]) // 2
                backgrounds.append(scaled.crop((left, top, left + size[0], top + size[1])))
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        args = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo",
                "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
                "-r", str(fps), "-i", "pipe:0", "-i", str(audio_path),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                "-t", f"{duration:.4f}", "-movflags", "+faststart", str(destination)]
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for frame_index in range(math.ceil(duration * fps)):
                now = frame_index / fps
                selected = next((i for i, cue in enumerate(cues)
                                 if cue["start"] <= now < cue["end"]), len(cues)-1)
                visual = reframe(backgrounds[selected], now - cues[selected]["start"])
                frame = caption_frame(visual, cues[selected]["text"])
                process.stdin.write(frame.tobytes())
            process.stdin.close()
            errors = process.stderr.read()
            code = process.wait()
            if code:
                raise ReelRenderError("FFmpeg: " + errors.decode("utf8", "replace")[-700:])
        except Exception:
            if process.poll() is None:
                process.kill()
                process.wait()
            destination.unlink(missing_ok=True)
            raise
        if not destination.is_file() or destination.stat().st_size < 1024:
            raise ReelRenderError("Arquivo MP4 não foi produzido")
        return {"output": str(destination), "duration": duration,
                "resolution": list(size), "fps": fps,
                "publication_approved": False,
                "visual_review_required": True,
                "visual_reframe_interval_seconds": 2.0,
                "distinct_source_images": len(images)}
    finally:
        for background in backgrounds:
            background.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narration-json", required=True)
    ap.add_argument("--images", nargs=4, required=True, metavar="IMAGE")
    ap.add_argument("--output", required=True)
    ap.add_argument("--ffmpeg", default="ffmpeg")
    args = ap.parse_args()
    try:
        data = json.loads(Path(args.narration_json).read_text(encoding="utf8"))
        result = render_reel(data["audio_path"], data["reel_caption_cues"],
                             args.images, args.output, ffmpeg=args.ffmpeg)
        report = Path(args.output).with_suffix(".review.json")
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    except (OSError, ValueError, KeyError, ReelRenderError) as exc:
        ap.exit(2, "Falha ao renderizar Reel: " + str(exc) + "\n")
    print("MP4 vertical criado para revisão, não aprovado para publicação.")


if __name__ == "__main__":
    main()
