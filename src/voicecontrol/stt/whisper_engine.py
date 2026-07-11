"""Speech-to-text using faster-whisper.

Load the model, transcribe a file, normalize the result to plain text.
No mic/recording logic here.

GPU-first with automatic CPU fallback: tries ``cuda``/``float16`` and falls
back to ``cpu``/``int8`` if CUDA is unavailable.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from faster_whisper import WhisperModel

from voicecontrol.config import settings
from voicecontrol.stt.engine import TranscriptionResult

logger = logging.getLogger(__name__)


class TranscriptionError(RuntimeError):
    """Raised when the audio file is missing or transcription fails."""


class WhisperEngine:
    """Thin wrapper around a faster-whisper model with lazy loading."""

    engine_name = "faster_whisper"

    def __init__(
        self,
        model_size: str = settings.WHISPER_MODEL_SIZE,
        device: str = settings.WHISPER_DEVICE,
        compute_type: str = settings.WHISPER_COMPUTE_TYPE,
        language: str | None = settings.WHISPER_LANGUAGE,
        beam_size: int = settings.WHISPER_BEAM_SIZE,
        vad_filter: bool = settings.WHISPER_VAD_FILTER,
        condition_on_previous_text: bool = settings.WHISPER_CONDITION_ON_PREVIOUS_TEXT,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self.condition_on_previous_text = condition_on_previous_text
        self._model: WhisperModel | None = None

    def load(self) -> None:
        """Load the model, falling back to CPU/int8 if CUDA is unavailable."""
        if self._model is not None:
            return

        try:
            logger.info(
                "Loading Whisper '%s' on %s (%s)",
                self.model_size, self.device, self.compute_type,
            )
            self._model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )
        except Exception as exc:
            if self.device != settings.WHISPER_CPU_DEVICE:
                logger.warning(
                    "GPU load failed (%s); falling back to CPU/%s.",
                    exc, settings.WHISPER_CPU_COMPUTE_TYPE,
                )
                self.device = settings.WHISPER_CPU_DEVICE
                self.compute_type = settings.WHISPER_CPU_COMPUTE_TYPE
                try:
                    self._model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=self.compute_type,
                    )
                except Exception as cpu_exc:
                    raise TranscriptionError(
                        "Failed to load Whisper on the configured device, and CPU fallback "
                        f"also failed: {cpu_exc}"
                    ) from cpu_exc
            else:
                raise TranscriptionError(f"Failed to load Whisper model: {exc}") from exc

    def transcribe_file(self, path: str | Path) -> TranscriptionResult:
        """Transcribe a WAV/audio file and return normalized text with metadata."""
        audio_path = Path(path)
        if not audio_path.is_file():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        self.load()
        assert self._model is not None

        try:
            started_at = time.perf_counter()
            segments, info = self._model.transcribe(
                str(audio_path),
                language=self.language,
                beam_size=self.beam_size,
                vad_filter=self.vad_filter,
                condition_on_previous_text=self.condition_on_previous_text,
            )
            text = "".join(segment.text for segment in segments).strip()
            duration_seconds = time.perf_counter() - started_at
        except Exception as exc:
            raise TranscriptionError(f"Transcription failed for {audio_path}: {exc}") from exc

        logger.info(
            "Transcribed %s (detected language=%s, p=%.2f)",
            audio_path.name, info.language, info.language_probability,
        )
        if not text:
            logger.warning("Transcription produced empty text for %s", audio_path)
        return TranscriptionResult(
            text=text,
            engine=self.engine_name,
            model=self.model_size,
            language=info.language,
            language_probability=info.language_probability,
            duration_seconds=duration_seconds,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    wav_path = settings.DEFAULT_RECORDING_PATH
    try:
        engine = WhisperEngine()
        result = engine.transcribe_file(wav_path)
        print(f"\nRecognized text:\n{result.text!r}")
    except TranscriptionError as exc:
        print(f"ERROR: {exc}")
