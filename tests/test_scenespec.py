import copy
import unittest
from universal_engine.scenespec import SceneError, validate, motion, fingerprint

SCENES = [
 {"version":1,"scene_id":"ocean-octopus","narration":"O polvo libera tinta e escapa.",
  "duration_target_seconds":6,"setting":{"kind":"underwater"},
  "actors":[{"id":"polvo","kind":"animal","asset_id":"octopus-v1","x":.2,"y":.5},
            {"id":"tubarao","kind":"animal","asset_id":"shark-v1","x":.8,"y":.5}],
  "timeline":[{"at":0,"action":"approach","target":"tubarao","towards":"polvo","duration":1.2},
              {"at":1.5,"action":"react","target":"polvo","emotion":"surprised"},
              {"at":2.0,"action":"emit_particles","target":"polvo","effect":"ink_cloud"},
              {"at":3.1,"action":"escape","target":"polvo","to_x":.05,"duration":2}],
  "visual_fact":"Polvos podem liberar tinta para confundir predadores."},
 {"version":1,"scene_id":"space-orbit","narration":"A Terra gira ao redor do Sol.",
  "duration_target_seconds":5,"setting":{"kind":"space"},
  "actors":[{"id":"terra","kind":"planet","asset_id":"earth-v1","x":.7,"y":.5},
            {"id":"sol","kind":"planet","asset_id":"sun-v1","x":.3,"y":.5}],
  "timeline":[{"at":0,"action":"rotate","target":"terra","duration":3,"degrees":360},
              {"at":3.1,"action":"highlight","target":"sol"}],
  "visual_fact":"A Terra completa uma orbita em aproximadamente um ano."},
 {"version":1,"scene_id":"technology-robot","narration":"Um robo identifica e separa objetos.",
  "duration_target_seconds":5,"setting":{"kind":"workshop"},
  "actors":[{"id":"robo","kind":"machine","asset_id":"arm-v1","x":.15,"y":.55},
            {"id":"peca","kind":"object","asset_id":"part-v1","x":.6,"y":.65}],
  "timeline":[{"at":0,"action":"move","target":"robo","to_x":.45,"duration":1.8},
              {"at":2.0,"action":"highlight","target":"peca"},
              {"at":3.0,"action":"move","target":"peca","to_x":.85,"duration":1.5}],
  "visual_fact":"Robos industriais podem separar pecas por sensores."},
]

class SceneSpecTests(unittest.TestCase):
 def test_three_unrelated_topics(self):
  hashes=set()
  for scene in SCENES:
   self.assertIs(validate(scene),scene)
   self.assertTrue(motion(scene,0))
   self.assertTrue(motion(scene,scene["duration_target_seconds"]-.001))
   hashes.add(fingerprint(scene))
  self.assertEqual(len(hashes),3)
 def test_motion_changes(self):
  s=SCENES[2]
  a=motion(s,.1)["robo"]["x"]
  b=motion(s,1.7)["robo"]["x"]
  self.assertGreater(b,a)
 def test_missing_actor_rejected(self):
  s=copy.deepcopy(SCENES[0])
  s["timeline"][0]["target"]="nao-existe"
  with self.assertRaises(SceneError):validate(s)
 def test_no_fake_unsupported_action(self):
  s=copy.deepcopy(SCENES[0])
  s["timeline"][0]["action"]="inventar_desenho"
  with self.assertRaises(SceneError):validate(s)
 def test_invalid_duration(self):
  s=copy.deepcopy(SCENES[0])
  s["timeline"][0]["duration"]=100
  with self.assertRaises(SceneError):validate(s)
 def test_order_enforced(self):
  s=copy.deepcopy(SCENES[0])
  s["timeline"][1]["at"]=-1
  with self.assertRaises(SceneError):validate(s)

 def test_enter_exit_opacity(self):
  s=copy.deepcopy(SCENES[0])
  s["timeline"]=[{"at":0,"action":"enter","target":"polvo","to_x":.5,"duration":2},
                 {"at":3,"action":"exit","target":"polvo","to_x":.9,"duration":2}]
  self.assertLess(motion(s,.1)["polvo"]["opacity"],.2)
  self.assertGreater(motion(s,2.1)["polvo"]["opacity"],.9)
  self.assertLess(motion(s,4.9)["polvo"]["opacity"],.2)

 def test_consecutive_moves_no_teleport(self):
  s=copy.deepcopy(SCENES[2])
  s["timeline"]=[
   {"at":0,"action":"move","target":"robo","to_x":.9,"duration":4},
   {"at":2,"action":"move","target":"robo","to_x":.2,"duration":2}
  ]
  before=motion(s,1.999)["robo"]["x"]
  after=motion(s,2.001)["robo"]["x"]
  self.assertLess(abs(before-after),.01,"Personagem teletransportou entre movimentos")
 def test_orbit_moves_planet_across_positions(self):
  s=copy.deepcopy(SCENES[1])
  s["timeline"]=[{"at":0,"action":"orbit","target":"terra","towards":"sol",
                  "duration":4,"degrees":180}]
  a=motion(s,.1)["terra"]
  b=motion(s,3.9)["terra"]
  self.assertGreater(abs(a["x"]-b["x"]),.4)
 def test_orbit_unknown_target_is_rejected(self):
  s=copy.deepcopy(SCENES[1])
  s["timeline"]=[{"at":0,"action":"orbit","target":"terra","towards":"missing"}]
  with self.assertRaises(SceneError):validate(s)

if __name__=="__main__":unittest.main()
