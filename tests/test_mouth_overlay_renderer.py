import unittest
from PIL import Image
from universal_engine.mouth_overlay import compose_mouth, MouthOverlayError
from universal_engine.layer_renderer import render_frame, RenderError


def scene():
    return {
        "version": 1, "scene_id": "talking", "narration": "Olá mundo.",
        "duration_target_seconds": 3, "visual_fact": "Pessoa falando",
        "actors": [{"id": "hero", "asset_id": "hero", "kind": "person",
                    "x": .5, "y": .5, "size": .4,
                    "mouth": {"asset_id": "mouth", "x": .5, "y": .5, "width": .3}}],
        "timeline": [{"action": "react", "target": "hero", "at": 2}]
    }


def assets():
    face = Image.new("RGBA", (100, 100), (120, 120, 120, 255))
    mouth = Image.new("RGBA", (30, 10), (255, 0, 0, 255))
    mouth.paste((0, 255, 0, 255), (10, 0, 20, 10))
    mouth.paste((0, 0, 255, 255), (20, 0, 30, 10))
    return {"hero": face, "mouth": mouth}


class MouthOverlayTests(unittest.TestCase):
    def test_overlay_changes_with_audio(self):
        art = assets()
        quiet = compose_mouth(art["hero"], art["mouth"],
                              {"window_ms": 50, "amplitudes": [0, .5]}, 0,
                              x=.5, y=.5, width=.3)
        loud = compose_mouth(art["hero"], art["mouth"],
                             {"window_ms": 50, "amplitudes": [0, .5]}, .05,
                             x=.5, y=.5, width=.3)
        self.assertNotEqual(quiet.getpixel((50, 50)), loud.getpixel((50, 50)))

    def test_renderer_uses_audio_envelope(self):
        bg = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        art = assets()
        quiet = render_frame(scene(), 0, bg, art, (320, 180),
                             mouth_envelope={"window_ms": 50, "amplitudes": [0, .5]})
        loud = render_frame(scene(), .05, bg, art, (320, 180),
                            mouth_envelope={"window_ms": 50, "amplitudes": [0, .5]})
        self.assertNotEqual(quiet.getpixel((160, 90)), loud.getpixel((160, 90)))

    def test_missing_envelope_rejected(self):
        with self.assertRaises(RenderError):
            render_frame(scene(), 0, Image.new("RGBA", (320, 180)), assets(), (320, 180))

    def test_out_of_bounds_mouth_rejected(self):
        art = assets()
        with self.assertRaises(MouthOverlayError):
            compose_mouth(art["hero"], art["mouth"],
                          {"window_ms": 50, "amplitudes": [0]}, 0,
                          x=0, y=0, width=.5)


if __name__ == "__main__":
    unittest.main()
