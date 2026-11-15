import unittest
from universal_engine.scenespec import validate, SceneError


def scene(action):
    return {"version": 1, "scene_id": "camera-params", "narration": "Veja o detalhe.",
            "duration_target_seconds": 5, "visual_fact": "Detalhe em destaque",
            "actors": [{"id": "object", "asset_id": "object-1", "kind": "object"}],
            "timeline": [{"action": action, "at": 0, "duration": 2}]}


class CameraParameterTests(unittest.TestCase):
    def test_camera_push_without_target(self):
        validate(scene("camera_push"))

    def test_camera_push_valid_target(self):
        s = scene("camera_push")
        s["timeline"][0]["target"] = "object"
        validate(s)

    def test_unknown_camera_target(self):
        s = scene("camera_push")
        s["timeline"][0]["target"] = "unknown"
        with self.assertRaises(SceneError):
            validate(s)

    def test_invalid_zooms(self):
        for zoom in (-1, 0, 2, float("nan"), float("inf"), "large"):
            with self.subTest(zoom=zoom):
                s = scene("camera_push")
                s["timeline"][0]["zoom"] = zoom
                with self.assertRaises(SceneError):
                    validate(s)

    def test_invalid_pan(self):
        for value in (-1, 2, float("nan"), "left"):
            with self.subTest(value=value):
                s = scene("camera_pan")
                s["timeline"][0]["to_x"] = value
                with self.assertRaises(SceneError):
                    validate(s)


if __name__ == "__main__":
    unittest.main()
