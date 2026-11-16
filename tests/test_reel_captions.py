import unittest
from PIL import Image
from universal_engine.reel_captions import caption_frame


class ReelCaptionTests(unittest.TestCase):
    def test_vertical_caption_changes_pixels_without_changing_dimensions(self):
        original = Image.new("RGB", (360, 640), (30, 50, 70))
        result = caption_frame(original, "A cidade que desapareceu")
        self.assertEqual(result.size, (360, 640))
        self.assertNotEqual(result.getpixel((180, 448)), original.getpixel((180, 448)))

    def test_horizontal_video_cannot_use_vertical_caption(self):
        with self.assertRaises(ValueError):
            caption_frame(Image.new("RGB", (640, 360)), "Texto")

    def test_empty_caption_preserves_original(self):
        original = Image.new("RGB", (360, 640))
        self.assertIs(caption_frame(original, ""), original)

    def test_excessively_long_caption_rejected(self):
        with self.assertRaises(ValueError):
            caption_frame(Image.new("RGB", (360, 640)), "A" * 161)


if __name__ == "__main__":
    unittest.main()
