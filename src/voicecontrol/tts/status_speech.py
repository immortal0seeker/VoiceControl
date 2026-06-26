"""Speak short prompts in response to status events."""

from __future__ import annotations

import logging

from voicecontrol.config import settings
from voicecontrol.events.status import StatusEvent, StatusPublisher, StatusType, Unsubscribe
from voicecontrol.tts.speaker import TextSpeaker, TtsError

logger = logging.getLogger(__name__)


class StatusSpeechSubscriber:
    """Subscribe to status events and speak concise feedback."""

    def __init__(
        self,
        speaker: TextSpeaker,
        publisher: StatusPublisher,
        enabled: bool = True,
    ) -> None:
        self.speaker = speaker
        self.enabled = enabled
        self._unsubscribe: Unsubscribe | None = publisher.subscribe(self._on_status)

    def close(self) -> None:
        """Unsubscribe from future status events."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    def _on_status(self, event: StatusEvent) -> None:
        if not self.enabled:
            return
        phrase = self._phrase_for(event)
        if phrase is None:
            return
        try:
            self.speaker.speak(phrase)
        except TtsError:
            logger.exception("TTS status speech failed for %s.", event.type)

    def _phrase_for(self, event: StatusEvent) -> str | None:
        if event.type == StatusType.WAKE:
            return "我在"
        if event.type == StatusType.RECORDING:
            return "请说"
        if event.type == StatusType.TRANSCRIBING:
            return "正在识别"
        if event.type == StatusType.SENDING:
            return "正在发送"
        if event.type == StatusType.DONE:
            return "已发送" if event.data.get("sent") else "完成"
        if event.type == StatusType.ERROR:
            return "出错了"
        return None


def create_status_speech_subscriber(
    publisher: StatusPublisher,
) -> StatusSpeechSubscriber | None:
    """Create the configured status speech subscriber, if TTS is enabled."""
    if not settings.TTS_ENABLED:
        return None
    speaker = TextSpeaker(
        enabled=True,
        rate=settings.TTS_RATE,
        volume=settings.TTS_VOLUME,
        voice=settings.TTS_VOICE,
    )
    return StatusSpeechSubscriber(speaker=speaker, publisher=publisher, enabled=True)
