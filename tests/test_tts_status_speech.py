from __future__ import annotations

import unittest
from unittest.mock import Mock
from unittest.mock import patch

from voicecontrol.events.status import StatusPublisher, StatusType
from voicecontrol.tts.status_speech import StatusSpeechSubscriber, create_status_speech_subscriber


class StatusSpeechSubscriberTests(unittest.TestCase):
    def test_subscriber_speaks_for_key_status_events(self) -> None:
        publisher = StatusPublisher()
        speaker = Mock()
        StatusSpeechSubscriber(speaker=speaker, publisher=publisher)

        publisher.publish(StatusType.WAKE)
        publisher.publish(StatusType.TRANSCRIBING)
        publisher.publish(StatusType.SENDING)
        publisher.publish(StatusType.DONE, data={"sent": True})

        self.assertEqual(
            [call.args[0] for call in speaker.speak.call_args_list],
            ["我在", "正在识别", "正在发送", "已发送"],
        )

    def test_subscriber_speaks_error_message(self) -> None:
        publisher = StatusPublisher()
        speaker = Mock()
        StatusSpeechSubscriber(speaker=speaker, publisher=publisher)

        publisher.publish(StatusType.ERROR, message="missing window")

        speaker.speak.assert_called_once_with("出错了")

    def test_disabled_subscriber_does_not_speak(self) -> None:
        publisher = StatusPublisher()
        speaker = Mock()
        StatusSpeechSubscriber(speaker=speaker, publisher=publisher, enabled=False)

        publisher.publish(StatusType.WAKE)

        speaker.speak.assert_not_called()

    def test_close_unsubscribes_from_publisher(self) -> None:
        publisher = StatusPublisher()
        speaker = Mock()
        subscriber = StatusSpeechSubscriber(speaker=speaker, publisher=publisher)

        subscriber.close()
        publisher.publish(StatusType.WAKE)

        speaker.speak.assert_not_called()

    def test_factory_uses_tts_settings(self) -> None:
        publisher = StatusPublisher()
        speaker = Mock()

        with (
            patch("voicecontrol.tts.status_speech.settings.TTS_ENABLED", True),
            patch("voicecontrol.tts.status_speech.settings.TTS_RATE", 2),
            patch("voicecontrol.tts.status_speech.settings.TTS_VOLUME", 80),
            patch("voicecontrol.tts.status_speech.settings.TTS_VOICE", "Huihui"),
            patch("voicecontrol.tts.status_speech.TextSpeaker", return_value=speaker) as speaker_class,
        ):
            subscriber = create_status_speech_subscriber(publisher)

        self.assertIsNotNone(subscriber)
        speaker_class.assert_called_once_with(
            enabled=True,
            rate=2,
            volume=80,
            voice="Huihui",
        )

    def test_factory_returns_none_when_tts_disabled(self) -> None:
        publisher = StatusPublisher()

        with (
            patch("voicecontrol.tts.status_speech.settings.TTS_ENABLED", False),
            patch("voicecontrol.tts.status_speech.TextSpeaker") as speaker_class,
        ):
            subscriber = create_status_speech_subscriber(publisher)

        self.assertIsNone(subscriber)
        speaker_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
