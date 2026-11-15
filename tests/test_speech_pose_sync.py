import unittest
from PIL import Image
from universal_engine.speech_pose_sync import speech_pose_time, speech_pose_frame, PoseSyncError


class SpeechPoseSyncTests(unittest.TestCase):
    def test_lead_in_and_end_hold(self):
        self.assertEqual(speech_pose_time(.2, 4, lead_in=.5, lead_out=.5), 0)
        self.assertEqual(speech_pose_time(5, 4, lead_in=.5, lead_out=.5), 3)

    def test_invalid_margins(self):
        for margins in ((2, 2), (-1, 0), (0, 4)):
            with self.subTest(margins=margins):
                with self.assertRaises(PoseSyncError):
                    speech_pose_time(1, 4, lead_in=margins[0], lead_out=margins[1])

    def test_pose_follows_speech_window(self):
        sheet = Image.new("RGBA", (20, 10), (255, 0, 0, 255))
        sheet.paste((0, 255, 0, 255), (10, 0, 20, 10))
        initial = speech_pose_frame(sheet, .2, 3, rows=1, columns=2,
                                    frames=2, fps=2, lead_in=.5)
        speaking = speech_pose_frame(sheet, 1, 3, rows=1, columns=2,
                                     frames=2, fps=2, lead_in=.5)
        self.assertNotEqual(initial.getpixel((5, 5)), speaking.getpixel((5, 5)))


if __name__ == "__main__":
    unittest.main()
