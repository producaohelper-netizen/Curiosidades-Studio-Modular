import unittest
from PIL import Image
from universal_engine.sprites import select_frame, SpriteError
class TestSprites(unittest.TestCase):
 def test_four_cell_animation(self):
  sheet=Image.new("RGBA",(80,80),(0,0,0,0))
  colors=["red","blue","green","yellow"]
  for i,color in enumerate(colors):
   patch=Image.new("RGBA",(40,40),color)
   sheet.paste(patch,((i%2)*40,(i//2)*40))
  a=select_frame(sheet,.01,rows=2,columns=2,frames=4,pose_fps=4)
  b=select_frame(sheet,.3,rows=2,columns=2,frames=4,pose_fps=4)
  self.assertNotEqual(a.getpixel((10,10)),b.getpixel((10,10)))
 def test_reject_nonuniform_grid(self):
  with self.assertRaises(SpriteError):
   select_frame(Image.new("RGB",(81,80)),.5,rows=2,columns=2,frames=4)
 def test_loop_is_consistent(self):
  sheet=Image.new("RGB",(80,80),"orange")
  self.assertEqual(select_frame(sheet,0,rows=2,columns=2,frames=4).tobytes(),
                   select_frame(sheet,1,rows=2,columns=2,frames=4).tobytes())
if __name__=="__main__":unittest.main()
