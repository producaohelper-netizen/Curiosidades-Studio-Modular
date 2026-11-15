import unittest
from PIL import Image,ImageChops,ImageDraw
from universal_engine.deformation import organic_sway, organic_swim

class DeformationTests(unittest.TestCase):
    def test_sway_preserves_head_and_moves_lower_tentacles(self):
        image=Image.new("RGBA",(220,220),(0,0,0,0))
        d=ImageDraw.Draw(image)
        d.ellipse((75,8,160,80),fill="#e35f33")
        for offset in [42,65,90,118,140]:
            d.line((110,70,offset,205),fill="#e35f33",width=13)
        first=organic_sway(image,0)
        second=organic_sway(image,.38)
        self.assertIsNotNone(ImageChops.difference(first,second).getbbox())
        # Head remains practically unchanged.
        head=ImageChops.difference(first.crop((70,0,170,55)),
                                   second.crop((70,0,170,55)))
        self.assertIsNone(head.getbbox())
    def test_swimming_tail_moves_but_head_is_stable(self):
        image=Image.new("RGBA",(260,110),(0,0,0,0))
        d=ImageDraw.Draw(image)
        d.polygon([(10,55),(65,20),(65,90)],fill="#4ab2df")
        d.ellipse((50,25,240,90),fill="#4ab2df")
        a=organic_swim(image,0,tail_side="left")
        b=organic_swim(image,.35,tail_side="left")
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
        self.assertEqual(a.size,image.size)
        self.assertEqual(b.size,image.size)
    def test_unknown_tail_side_rejected(self):
        with self.assertRaises(ValueError):
            organic_swim(Image.new("RGBA",(100,50)),.1,tail_side="up")
    def test_periodic_loop_is_seamless(self):
        im=Image.new("RGBA",(200,170),(255,80,30,240))
        a=organic_sway(im,0)
        b=organic_sway(im,1.7)
        self.assertEqual(a.tobytes(),b.tobytes())
