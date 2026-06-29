"""Shared speech-to-text engine interfaces and result metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TranscriptionResult:
    """Normalized STT output plus metadata useful for diagnostics/history."""

    text: str
    engine: str
    model: str
    language: str | None = None
    language_probability: float | None = None
    duration_seconds: float | None = None

    def to_history_metadata(self) -> dict[str, object]:
        """Return stable history keys for this transcription."""
        return {
            "stt_engine": self.engine,
            "stt_model": self.model,
            "stt_language": self.language,
            "stt_language_probability": self.language_probability,
        }


class STTEngine(Protocol):
    """Minimal interface consumed by the voice pipeline."""

    def load(self) -> None:
        """Load model resources if needed."""

    def transcribe_file(self, path: str | Path) -> TranscriptionResult:
        """Transcribe an audio file and return text with STT metadata."""
