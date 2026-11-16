import unittest
from universal_engine.reel_caption_cards import caption_cards, caption_at
from PIL import Image
from universal_engine.reel_captions import caption_frame


class CaptionCardTests(unittest.TestCase):
    def test_long_narration_fits_small_portrait(self):
        narration = ("Dois desses corações ajudam a enviar sangue às brânquias, "
                     "enquanto outro impulsiona o sangue pelo restante do corpo. "
                     "Uma descoberta que surpreende quem estuda animais marinhos.")
        cards = caption_cards(narration)
        self.assertGreater(len(cards), 1)
        self.assertEqual(" ".join(cards), narration)
        for card in cards:
            rendered = caption_frame(Image.new("RGB", (180, 320)), card)
            self.assertEqual(rendered.size, (180, 320))
        self.assertEqual(caption_at(narration, 0, 10), cards[0])
        self.assertEqual(caption_at(narration, 9.99, 10), cards[-1])

    def test_invalid_time_rejected(self):
        with self.assertRaises(ValueError):
            caption_at("teste", 0, 0)


if __name__ == "__main__":
    unittest.main()
