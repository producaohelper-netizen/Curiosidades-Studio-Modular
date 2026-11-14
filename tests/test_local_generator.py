import json
import tempfile
import unittest
from pathlib import Path
from io import BytesIO
from PIL import Image
from universal_engine.local_generator import generate, prepare_workflow, GenerationError

class LocalImageGeneratorTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.template=Path(self.temp.name)/"workflow_api.json"
  self.template.write_text('{"1":{"class_type":"CLIPTextEncode","inputs":{"text":"{{PROMPT}}"}},"2":{"class_type":"KSampler","inputs":{"seed":{{SEED}}}}}',encoding="utf8")
 def test_prompt_json_escaped(self):
  workflow=prepare_workflow(self.template,'a "surprised" octopus with \\bubbles',77)
  self.assertEqual(workflow["1"]["inputs"]["text"],'a "surprised" octopus with \\bubbles')
  self.assertEqual(workflow["2"]["inputs"]["seed"],77)
 def test_end_to_end_with_mock_comfy_api(self):
  buffer=BytesIO()
  Image.new("RGB",(32,32),"teal").save(buffer,format="PNG")
  urls=[]
  def fake_json(url,method="GET",payload=None):
   urls.append(url)
   if url.endswith("/prompt"):
    self.assertEqual(payload["prompt"]["2"]["inputs"]["seed"],123)
    return {"prompt_id":"abc"}
   return {"abc":{"outputs":{"save":{"images":[{"filename":"result.png","subfolder":"","type":"output"}]}}}}
  def fake_bytes(url):
   self.assertIn("filename=result.png",url)
   return buffer.getvalue()
  result=generate("a cartoon octopus escapes a shark",
                  self.template,Path(self.temp.name)/"image.png",
                  seed=123,request_json=fake_json,request_bytes=fake_bytes,interval=0)
  self.assertTrue(Path(result.file).is_file())
  with Image.open(result.file) as img:self.assertEqual(img.size,(32,32))
  self.assertEqual(len(urls),2)
 def test_reject_nonlocal_endpoint(self):
  with self.assertRaises(GenerationError):
   generate("a cartoon octopus escapes a shark",self.template,"x.png",
            server="https://unexpected.example.com")
 def test_no_silent_fallback(self):
  with self.assertRaises(GenerationError):
   generate("a cartoon octopus escapes a shark",self.template,"x.png",
            request_json=lambda url,**kw: {"error":"unavailable"})
 def test_invalid_workflow_rejected(self):
  self.template.write_text('{"foo":"bar"}')
  with self.assertRaises(GenerationError):
   prepare_workflow(self.template,"descriptive prompt",1)
if __name__=="__main__":
 unittest.main()
