"""Windows text-to-speech speaker using SAPI."""

from __future__ import annotations

import logging
from typing import Any

import win32com.client

logger = logging.getLogger(__name__)

SPF_ASYNC = 1
SPF_PURGEBEFORESPEAK = 2


class TtsError(RuntimeError):
    """Raised when text-to-speech cannot be initialized or used."""


class TextSpeaker:
    """Small wrapper around the Windows SAPI voice engine."""

    def __init__(
        self,
        enabled: bool = True,
        rate: int = 0,
        volume: int = 100,
        voice: str | None = None,
    ) -> None:
        self.enabled = enabled
        self.rate = rate
        self.volume = volume
        self.voice = voice
        self._engine: Any | None = None

    def _voice_engine(self) -> Any:
        if self._engine is None:
            try:
                engine = win32com.client.Dispatch("SAPI.SpVoice")
                engine.Rate = self.rate
                engine.Volume = self.volume
                if self.voice:
                    self._select_voice(engine, self.voice)
            except Exception as exc:
                raise TtsError(f"Failed to initialize Windows SAPI TTS: {exc}") from exc
            self._engine = engine
        return self._engine

    def _select_voice(self, engine: Any, voice_name: str) -> None:
        needle = voice_name.lower()
        for voice in engine.GetVoices():
            description = voice.GetDescription()
            if needle in description.lower():
                engine.Voice = voice
                return
        logger.warning("Configured TTS voice not found: %s", voice_name)

    def speak(self, text: str) -> None:
        """Speak ``text`` asynchronously when TTS is enabled."""
        if not self.enabled:
            return
        message = text.strip()
        if not message:
            return
        try:
            self._voice_engine().Speak(message, SPF_ASYNC)
        except Exception as exc:
            raise TtsError(f"Failed to speak text: {exc}") from exc

    def stop(self) -> None:
        """Stop any queued/current speech."""
        if not self.enabled:
            return
        try:
            self._voice_engine().Speak("", SPF_ASYNC | SPF_PURGEBEFORESPEAK)
        except Exception as exc:
            raise TtsError(f"Failed to stop speech: {exc}") from exc
