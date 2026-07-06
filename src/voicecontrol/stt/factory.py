"""Factory for speech-to-text engine providers."""

from __future__ import annotations

from typing import Any

from voicecontrol.config import settings
from voicecontrol.config.manager import load_config
from voicecontrol.stt.engine import STTEngine
from voicecontrol.stt.sensevoice_engine import SenseVoiceEngine
from voicecontrol.stt.whisper_engine import WhisperEngine


def create_stt_engine(config: dict[str, Any] | None = None) -> STTEngine:
    """Create the configured STT engine without loading the model."""
    resolved_config = load_config() if config is None else config
    stt_config = resolved_config["stt"]
    provider = stt_config.get("provider", settings.STT_PROVIDER)

    if provider == "faster_whisper":
        return WhisperEngine(
            model_size=stt_config.get("whisper_model_size", settings.WHISPER_MODEL_SIZE),
            device=stt_config.get("whisper_device", settings.WHISPER_DEVICE),
            compute_type=stt_config.get("whisper_compute_type", settings.WHISPER_COMPUTE_TYPE),
            language=stt_config.get("whisper_language", settings.WHISPER_LANGUAGE),
            beam_size=stt_config.get("whisper_beam_size", settings.WHISPER_BEAM_SIZE),
            vad_filter=stt_config.get("whisper_vad_filter", settings.WHISPER_VAD_FILTER),
            condition_on_previous_text=stt_config.get(
                "whisper_condition_on_previous_text",
                settings.WHISPER_CONDITION_ON_PREVIOUS_TEXT,
            ),
        )

    if provider == "funasr_sensevoice":
        return SenseVoiceEngine(
            model=stt_config.get("sensevoice_model", settings.SENSEVOICE_MODEL),
            device=stt_config.get("sensevoice_device", settings.SENSEVOICE_DEVICE),
            language=stt_config.get("sensevoice_language", settings.SENSEVOICE_LANGUAGE),
        )

    raise ValueError(
        f"Unknown STT provider {provider!r}; expected one of: faster_whisper, funasr_sensevoice"
    )
