import unittest
from universal_engine.reel_visual_sequence import normalize_images, image_index


class VisualSequenceTests(unittest.TestCase):
    def test_supports_single_and_multiple_images_per_section(self):
        self.assertEqual(normalize_images(["a.png", ["b.png", "c.png"]], 2),
                         [["a.png"], ["b.png", "c.png"]])
        self.assertEqual(image_index(0, 2), 0)
        self.assertEqual(image_index(2, 2), 1)
        self.assertEqual(image_index(4, 2), 0)

    def test_rejects_missing_section_images(self):
        with self.assertRaises(ValueError):
            normalize_images([[]], 1)
        with self.assertRaises(ValueError):
            normalize_images(["one.png"], 2)


if __name__ == "__main__":
    unittest.main()
