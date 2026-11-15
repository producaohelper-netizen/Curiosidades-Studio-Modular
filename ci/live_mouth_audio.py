"""Real Piper speech -> three mouth poses -> actual H.264 clip.

Synthetic art is used only to verify end-to-end synchronization; this is
not an artistic sample or a production episode.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw
from universal_engine.narration import generate_piper
from universal_engine.layer_renderer import render_clip
from universal_engine.mouth_sync import wav_envelope, mouth_pose_at


def main():
    root = Path("live-mouth")
    root.mkdir(exist_ok=True)
    voice = Path("voice/pt_BR-faber-medium.onnx")
    speech = generate_piper(
        "Você sabia que o polvo pode mudar de cor e se esconder de seus predadores?",
        voice, root / "speech.wav", timeout=300)
    background = Image.new("RGBA", (960, 540), "#14354b")
    background.save(root / "background.png")
    hero = Image.new("RGBA", (200, 200))
    ImageDraw.Draw(hero).ellipse((15, 10, 185, 190), fill="#ffcf91")
    hero.save(root / "hero.png")
    mouths = Image.new("RGBA", (90, 30))
    painter = ImageDraw.Draw(mouths)
    painter.rounded_rectangle((5, 13, 25, 17), radius=2, fill="#44252b")
    painter.ellipse((35, 8, 55, 22), fill="#44252b")
    painter.ellipse((64, 2, 86, 28), fill="#44252b")
    mouths.save(root / "mouth.png")
    scene = {
        "version": 1, "scene_id": "real-audio-mouth-smoke",
        "narration": "Você sabia que o polvo pode mudar de cor e se esconder de seus predadores?",
        "duration_target_seconds": speech["duration"],
        "visual_fact": "Um narrador fala durante o teste de sincronização",
        "visual_style": "cartoon",
        "actors": [{"id": "narrador", "asset_id": "hero", "kind": "person",
                    "x": .5, "y": .5, "size": .5,
                    "mouth": {"asset_id": "mouth", "x": .5, "y": .64, "width": .32}}],
        "timeline": [{"action": "react", "at": 0, "target": "narrador"}]
    }
    envelope = wav_envelope(speech["path"])
    poses = [mouth_pose_at(envelope, t / 20) for t in range(int(speech["duration"] * 20))]
    if len(set(poses)) < 2:
        raise RuntimeError("Voz real nao provocou mudanca de boca")
    result = render_clip(scene, root / "background.png",
                         {"hero": root / "hero.png", "mouth": root / "mouth.png"},
                         speech["path"], root / "mouth_real_audio.mp4",
                         fps=24, size=(960, 540))
    report = {"clip": result, "mouth_pose_counts": {str(i): poses.count(i) for i in range(3)},
              "real_voice": True, "artistic_approval": "NOT_PERFORMED",
              "purpose": "Short technical smoke test only"}
    (root / "report.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
