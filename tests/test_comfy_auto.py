import json
import tempfile
import unittest
from pathlib import Path
from universal_engine.comfy_auto import (
    auto_workflow, make_workflow, checkpoints, ComfySetupError,
)
from universal_engine.local_generator import prepare_workflow

class AutoComfyTests(unittest.TestCase):
    def test_choose_installed_illustration_model(self):
        def fake(url):
            self.assertTrue(url.endswith("/models/checkpoints"))
            return ["standard-v1.safetensors","my-cartoon-v3.safetensors"]
        with tempfile.TemporaryDirectory() as temp:
            result=auto_workflow(Path(temp)/"workflow.json",fetch=fake)
            self.assertEqual(result["checkpoint"],"my-cartoon-v3.safetensors")
            graph=prepare_workflow(result["workflow"],
                'A cartoon octopus with "ink"!',12345)
            self.assertEqual(graph["3"]["inputs"]["seed"],12345)
            self.assertIsInstance(graph["3"]["inputs"]["seed"],int)
            self.assertIn("octopus",graph["6"]["inputs"]["text"])
            self.assertEqual(graph["4"]["inputs"]["ckpt_name"],"my-cartoon-v3.safetensors")
    def test_missing_checkpoint_blocks_generation(self):
        with self.assertRaises(ComfySetupError):
            checkpoints(fetch=lambda url:[])
    def test_sdxl_uses_appropriate_dimensions(self):
        with tempfile.TemporaryDirectory() as temp:
            res=auto_workflow(Path(temp)/"xl.json",
                fetch=lambda url:["sdxl-base-v1.safetensors"])
            graph=json.loads(Path(res["workflow"]).read_text())
            self.assertEqual(graph["5"]["inputs"]["width"],1024)
