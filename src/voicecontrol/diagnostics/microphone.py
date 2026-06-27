"""Microphone diagnostic recording."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from voicecontrol.audio.recorder import record, save_wav
from voicecontrol.config import settings
from voicecontrol.diagnostics.store import DiagnosticResult, append_diagnostic_result


def _audio_levels(audio: np.ndarray) -> tuple[float, float]:
    if audio.size == 0:
        return 0.0, 0.0
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio.astype("float64")))))
    return peak, rms


def run_microphone_test(
    seconds: float = 2.0,
    wav_path: str | Path | None = None,
    diagnostic_path: str | Path | None = None,
) -> DiagnosticResult:
    """Record a short sample, save it, and store level diagnostics."""
    output_path = Path(wav_path) if wav_path is not None else settings.new_recording_path("mic_test")
    try:
        audio = record(seconds=seconds)
        saved = save_wav(audio, output_path)
        peak, rms = _audio_levels(audio)
        result = DiagnosticResult(
            name="microphone",
            status="ok",
            details={
                "seconds": seconds,
                "wav_path": str(saved),
                "peak": peak,
                "rms": rms,
            },
        )
    except Exception as exc:
        result = DiagnosticResult(
            name="microphone",
            status="error",
            details={"seconds": seconds, "wav_path": str(output_path)},
            error=str(exc),
        )
    append_diagnostic_result(result, path=diagnostic_path)
    return result
