from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from voicecontrol.tts.speaker import TextSpeaker


class TextSpeakerTests(unittest.TestCase):
    def test_speak_uses_windows_sapi_voice(self) -> None:
        voice = Mock()

        with patch("voicecontrol.tts.speaker.win32com.client.Dispatch", return_value=voice) as dispatch:
            speaker = TextSpeaker(enabled=True, rate=2, volume=80)
            speaker.speak("我在")

        dispatch.assert_called_once_with("SAPI.SpVoice")
        self.assertEqual(voice.Rate, 2)
        self.assertEqual(voice.Volume, 80)
        voice.Speak.assert_called_once_with("我在", 1)

    def test_disabled_speaker_does_not_create_voice(self) -> None:
        with patch("voicecontrol.tts.speaker.win32com.client.Dispatch") as dispatch:
            speaker = TextSpeaker(enabled=False)
            speaker.speak("不会播报")

        dispatch.assert_not_called()

    def test_speak_can_wait_for_windows_sapi_to_finish(self) -> None:
        voice = Mock()

        with patch("voicecontrol.tts.speaker.win32com.client.Dispatch", return_value=voice):
            speaker = TextSpeaker(enabled=True)
            speaker.speak("我在", wait=True)

        voice.Speak.assert_called_once_with("我在", 0)

    def test_blank_text_is_ignored(self) -> None:
        with patch("voicecontrol.tts.speaker.win32com.client.Dispatch") as dispatch:
            speaker = TextSpeaker(enabled=True)
            speaker.speak("   ")

        dispatch.assert_not_called()

    def test_stop_purges_current_speech(self) -> None:
        voice = Mock()

        with patch("voicecontrol.tts.speaker.win32com.client.Dispatch", return_value=voice):
            speaker = TextSpeaker(enabled=True)
            speaker.stop()

        voice.Speak.assert_called_once_with("", 3)


if __name__ == "__main__":
    unittest.main()
