import unittest
from PIL import Image
from universal_engine.layer_renderer import render_frame


def make_scene():
    return {
        "version": 1, "scene_id": "pose-integration",
        "narration": "O personagem se movimenta.",
        "duration_target_seconds": 5,
        "visual_fact": "O personagem se movimenta",
        "visual_style": "cartoon",
        "actors": [{
            "id": "hero", "asset_id": "hero-v1", "kind": "person",
            "x": .5, "y": .5, "size": .3,
            "sprite": {"rows": 1, "columns": 2, "frames": 2,
                       "fps": 2, "loop": False}
        }],
        "timeline": [{"action": "react", "at": 4, "target": "hero"}]
    }


class RendererPoseIntegrationTests(unittest.TestCase):
    def test_rendered_frames_change_with_pose(self):
        sheet = Image.new("RGBA", (40, 20), (255, 0, 0, 255))
        sheet.paste((0, 255, 0, 255), (20, 0, 40, 20))
        bg = Image.new("RGBA", (320, 180), (20, 20, 20, 255))
        scene = make_scene()
        first = render_frame(scene, 0, bg, {"hero-v1": sheet}, (320, 180))
        second = render_frame(scene, 1, bg, {"hero-v1": sheet}, (320, 180))
        self.assertNotEqual(first.getpixel((160, 90)), second.getpixel((160, 90)))

    def test_pose_hold_first_keeps_initial_frame(self):
        sheet = Image.new("RGBA", (40, 20), (255, 0, 0, 255))
        sheet.paste((0, 255, 0, 255), (20, 0, 40, 20))
        bg = Image.new("RGBA", (320, 180), (20, 20, 20, 255))
        scene = make_scene()
        scene["actors"][0]["sprite"]["hold_first"] = 2
        first = render_frame(scene, 0, bg, {"hero-v1": sheet}, (320, 180))
        held = render_frame(scene, 1, bg, {"hero-v1": sheet}, (320, 180))
        self.assertEqual(first.getpixel((160, 90)), held.getpixel((160, 90)))


if __name__ == "__main__":
    unittest.main()
