import unittest
from universal_engine.storyboard_planner import plan_script,plan_batch,split_narration,PlanningError

def mock_model(prompt):
 import json,re
 marker=prompt.split("Falas (não altere nem reescreva; serão inseridas pelo programa):")[-1].strip()
 entries=json.loads(marker)
 return {"scenes":[{
     "setting":{"kind":"underwater"},
     "actors":[{"id":"octopus","kind":"animal","asset_id":"octopus-v1","x":.25,"y":.6},
               {"id":"shark","kind":"animal","asset_id":"shark-v1","x":.75,"y":.5}],
     "timeline":[{"at":0,"action":"approach","target":"shark","towards":"octopus","duration":.9},
                 {"at":1,"action":"react","target":"octopus","emotion":"surprised"}],
     "visual_fact":"Octopus ink can confuse predators.",
     "visual_query_en":"A cartoon octopus in a bright coral reef facing a blue shark, expressive faces.",
     "search_terms_en":"octopus shark reef"
   } for x in entries]}
class PlannerTests(unittest.TestCase):
 def test_no_narration_rewriting(self):
  story="O polvo solta tinta. Depois ele se esconde. O tubarão procura."
  result=plan_script(story,generator=mock_model,max_words=6)
  self.assertEqual(" ".join(x["narration"] for x in result["scenes"]),story)
  self.assertEqual(len(result["scenes"]),3)
  self.assertTrue(result["requires_real_audio_timing"])
  self.assertEqual(result["scenes"][0]["visual_query_en"][:8],"A cartoo")
 def test_more_than_five_scenes_in_batches(self):
  story=" ".join(f"Cena {i}: um planeta gira." for i in range(12))
  result=plan_script(story,generator=mock_model,max_words=5)
  self.assertGreaterEqual(len(result["scenes"]),12)
 def test_bad_model_fails_not_hallucinates(self):
  with self.assertRaises(PlanningError):
   plan_batch(["O polvo foge"],generator=lambda p:{"scenes":[]})
 def test_unsuitable_actors_fail_closed(self):
  def bad(prompt):
   x=mock_model(prompt)
   x["scenes"][0]["timeline"][0]["target"]="made_up"
   return x
  with self.assertRaises(PlanningError):
   plan_batch(["O polvo foge"],generator=bad)
 def test_short_exclamation_joins_following_scene(self):
  phrase="Uau! O polvo se esconde entre as pedras do fundo do mar."
  chunks=split_narration(phrase,max_words=15)
  self.assertEqual(" ".join(chunks),phrase)
  self.assertEqual(len(chunks),1)
 def test_ollama_receives_duration_for_each_scene(self):
  def check_context(prompt):
   import json
   data=json.loads(prompt.split("Falas (não altere nem reescreva; serão inseridas pelo programa):")[-1].strip())
   self.assertIn("duration_seconds",data[0])
   return mock_model(prompt)
  plan_batch(["O polvo foge do tubarão quando percebe o perigo."],
             generator=check_context)
 def test_empty_story(self):
  with self.assertRaises(PlanningError):split_narration("")
if __name__=="__main__":unittest.main()
