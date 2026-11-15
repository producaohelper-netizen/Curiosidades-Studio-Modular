"""Regressions for universal camera actions and invalid timing."""
import copy
import unittest

from universal_engine.scenespec import SceneError, validate


def scene():
    return {
        "version": 1, "scene_id": "camera-regression",
        "narration": "Um exemplo de movimento de câmera.",
        "duration_target_seconds": 8,
        "visual_fact": "A câmera se aproxima do objeto.",
        "actors": [{"id": "subject", "asset_id": "subject-v1", "kind": "object",
                    "x": 0.5, "y": 0.5}],
        "timeline": [{"at": 0, "action": "camera_push", "duration": 2},
                     {"at": 3, "action": "react", "target": "subject"}]
    }


class CameraTimingTests(unittest.TestCase):
    def test_camera_push_does_not_require_actor_target(self):
        self.assertEqual(validate(scene())["scene_id"], "camera-regression")

    def test_unknown_actor_is_still_rejected(self):
        value = scene()
        value["timeline"][1]["target"] = "missing"
        with self.assertRaises(SceneError):
            validate(value)

    def test_infinite_duration_rejected(self):
        for invalid in (float("inf"), float("-inf"), float("nan")):
            with self.subTest(invalid=invalid):
                value = scene()
                value["timeline"][0]["duration"] = invalid
                with self.assertRaises(SceneError):
                    validate(value)


if __name__ == "__main__":
    unittest.main()
