"""Speech-to-text using FunASR SenseVoice."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any, Callable

from voicecontrol.config import settings
from voicecontrol.stt.engine import TranscriptionResult

logger = logging.getLogger(__name__)

_SENSEVOICE_TAG_RE = re.compile(r"<\|[^|]*\|>")


class SenseVoiceError(RuntimeError):
    """Raised when SenseVoice cannot load or transcribe."""


class SenseVoiceEngine:
    """Thin wrapper around FunASR SenseVoice with lazy loading."""

    engine_name = "funasr_sensevoice"

    def __init__(
        self,
        model: str = settings.SENSEVOICE_MODEL,
        device: str = settings.SENSEVOICE_DEVICE,
        language: str | None = settings.SENSEVOICE_LANGUAGE,
        vad_model: str = "fsmn-vad",
        vad_max_single_segment_time: int = 30000,
        automodel_factory: Callable[..., object] | None = None,
    ) -> None:
        self.model = model
        self.device = device
        self.language = language
        self.vad_model = vad_model
        self.vad_max_single_segment_time = vad_max_single_segment_time
        self._automodel_factory = automodel_factory
        self._model: object | None = None

    @property
    def runtime_model(self) -> str:
        """Return the model identifier expected by FunASR."""
        if "/" in self.model:
            return self.model
        if self.model == "SenseVoiceSmall":
            return "iic/SenseVoiceSmall"
        return self.model

    def _load_automodel_factory(self) -> Callable[..., object]:
        if self._automodel_factory is not None:
            return self._automodel_factory
        try:
            from funasr import AutoModel
        except (ImportError, ModuleNotFoundError, PermissionError) as exc:
            raise SenseVoiceError(
                "SenseVoice runtime is not installed or incomplete. "
                'Install the optional extra with: .venv\\Scripts\\pip.exe install -e ".[sensevoice]". '
                "Also ensure ffmpeg is available."
            ) from exc
        return AutoModel

    def load(self) -> None:
        """Load the SenseVoice model if needed."""
        if self._model is not None:
            return

        automodel_factory = self._load_automodel_factory()
        try:
            logger.info("Loading SenseVoice '%s' on %s", self.model, self.device)
            self._model = automodel_factory(
                model=self.runtime_model,
                vad_model=self.vad_model,
                vad_kwargs={"max_single_segment_time": self.vad_max_single_segment_time},
                device=self.device,
                disable_update=True,
            )
        except (ImportError, ModuleNotFoundError, PermissionError) as exc:
            raise SenseVoiceError(
                "SenseVoice runtime is not installed or incomplete. "
                'Install the optional extra with: .venv\\Scripts\\pip.exe install -e ".[sensevoice]". '
                "Also ensure ffmpeg is available."
            ) from exc
        except Exception as exc:
            raise SenseVoiceError(f"Failed to load SenseVoice model: {exc}") from exc

    def transcribe_file(self, path: str | Path) -> TranscriptionResult:
        """Transcribe an audio file with SenseVoice and return normalized metadata."""
        audio_path = Path(path)
        if not audio_path.is_file():
            raise SenseVoiceError(f"Audio file not found: {audio_path}")

        self.load()
        assert self._model is not None

        try:
            started_at = time.perf_counter()
            generate_kwargs: dict[str, Any] = {
                "input": str(audio_path),
                "batch_size": 1,
            }
            if self.language:
                generate_kwargs["language"] = self.language
            raw_result = self._model.generate(**generate_kwargs)  # type: ignore[attr-defined]
            duration_seconds = time.perf_counter() - started_at
        except Exception as exc:
            raise SenseVoiceError(f"SenseVoice transcription failed for {audio_path}: {exc}") from exc

        text = _normalize_sensevoice_text(_extract_text(raw_result))
        if not text:
            logger.warning("SenseVoice transcription produced empty text for %s", audio_path)
        return TranscriptionResult(
            text=text,
            engine=self.engine_name,
            model=self.model,
            language=self.language,
            duration_seconds=duration_seconds,
        )


def _extract_text(raw_result: object) -> str:
    """Extract text from the FunASR result shape."""
    if isinstance(raw_result, list) and raw_result:
        first = raw_result[0]
        if isinstance(first, dict):
            value = first.get("text", "")
            return str(value)
    if isinstance(raw_result, dict):
        value = raw_result.get("text", "")
        return str(value)
    return ""


def _normalize_sensevoice_text(text: str) -> str:
    """Remove SenseVoice control tags and surrounding whitespace."""
    return _SENSEVOICE_TAG_RE.sub("", text).strip()
