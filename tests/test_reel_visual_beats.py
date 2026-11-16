import unittest
from PIL import Image
from universal_engine.reel_visual_beats import reframe


class VisualBeatTests(unittest.TestCase):
    def test_reframes_every_two_seconds_without_changing_dimensions(self):
        image = Image.new("RGB", (100, 180), "black")
        for x in range(100):
            for y in range(180):
                image.putpixel((x, y), (x * 2, y, 30))
        first = reframe(image, 0)
        second = reframe(image, 2)
        third = reframe(image, 4)
        self.assertEqual(first.size, (100, 180))
        self.assertEqual(second.size, first.size)
        self.assertNotEqual(first.tobytes(), second.tobytes())
        self.assertNotEqual(second.tobytes(), third.tobytes())
        self.assertEqual(reframe(image, 2).tobytes(), second.tobytes())

    def test_rejects_outside_editorial_interval(self):
        with self.assertRaises(ValueError):
            reframe(Image.new("RGB", (20, 40)), 0, interval=4)


if __name__ == "__main__":
    unittest.main()
