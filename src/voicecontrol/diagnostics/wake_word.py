"""Wake-word diagnostic helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from voicecontrol.config import settings
from voicecontrol.diagnostics.store import DiagnosticResult, append_diagnostic_result
from voicecontrol.wake_word.detector import WakeWordDetector


def _to_int16_mono(audio: np.ndarray) -> np.ndarray:
    samples = np.asarray(audio)
    if samples.ndim > 1:
        samples = samples[:, 0]
    if samples.dtype == np.int16:
        return samples
    clipped = np.clip(samples.astype("float32"), -1.0, 1.0)
    return (clipped * 32767).astype("int16")


def run_wake_word_file_test(
    wav_path: str | Path,
    detector: WakeWordDetector | None = None,
    frame_samples: int = settings.WAKE_FRAME_SAMPLES,
    diagnostic_path: str | Path | None = None,
) -> DiagnosticResult:
    """Score a WAV file with the wake-word detector and store diagnostics."""
    source_path = Path(wav_path)
    try:
        audio, sample_rate = sf.read(source_path, dtype="int16")
        samples = _to_int16_mono(np.asarray(audio))
        wake_detector = detector or WakeWordDetector()
        scores: list[float] = []
        for start in range(0, samples.size - frame_samples + 1, frame_samples):
            frame = samples[start:start + frame_samples]
            scores.append(float(wake_detector.score(frame)))
        max_score = max(scores, default=0.0)
        threshold = float(getattr(wake_detector, "threshold", settings.WAKE_THRESHOLD))
        result = DiagnosticResult(
            name="wake_word",
            status="ok",
            details={
                "wav_path": str(source_path),
                "sample_rate": int(sample_rate),
                "frames": len(scores),
                "max_score": max_score,
                "threshold": threshold,
                "detected": max_score >= threshold,
            },
        )
    except Exception as exc:
        result = DiagnosticResult(
            name="wake_word",
            status="error",
            details={"wav_path": str(source_path)},
            error=str(exc),
        )
    append_diagnostic_result(result, path=diagnostic_path)
    return result
