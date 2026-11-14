import unittest
from PIL import Image,ImageChops
from universal_engine.camera import apply_camera,camera_transform

class CameraTests(unittest.TestCase):
 def test_focus_on_actor(self):
  scene={"timeline":[{"at":1,"action":"camera_push","target":"dog","zoom":1.5,"duration":2}]}
  pos={"dog":{"x":.8,"y":.3}}
  z,c=camera_transform(scene,2.8,pos)
  self.assertGreater(z,1.3)
  self.assertGreater(c[0],.5)
 def test_camera_changes_output(self):
  image=Image.new("RGB",(500,300),"black")
  for x in range(200,400):
   for y in range(80,200):image.putpixel((x,y),(x%255,y%255,120))
  scene={"timeline":[{"at":0,"action":"camera_push","target":"dog","zoom":1.6,"duration":2}]}
  a=apply_camera(image,scene,0,{"dog":{"x":.7,"y":.5}})
  b=apply_camera(image,scene,1.8,{"dog":{"x":.7,"y":.5}})
  self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
 def test_zoom_clamped(self):
  s={"timeline":[{"at":0,"action":"camera_push","target":"x","zoom":100,"duration":1}]}
  zoom,c=camera_transform(s,1,{"x":{"x":.99,"y":.99}})
  self.assertLessEqual(zoom,1.8)
if __name__=="__main__":unittest.main()
