"""VAD diagnostic helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from voicecontrol.diagnostics.store import DiagnosticResult, append_diagnostic_result
from voicecontrol.vad.silero_vad import EndpointDetector


def run_vad_file_test(
    wav_path: str | Path,
    detector: EndpointDetector | None = None,
    diagnostic_path: str | Path | None = None,
) -> DiagnosticResult:
    """Run endpoint detection over a WAV file and store a diagnostic result."""
    source_path = Path(wav_path)
    try:
        audio, sample_rate = sf.read(source_path, dtype="float32")
        samples = np.asarray(audio, dtype="float32").reshape(-1)
        endpoint = detector or EndpointDetector()
        state = endpoint.update(samples)
        result = DiagnosticResult(
            name="vad",
            status="ok",
            details={
                "wav_path": str(source_path),
                "sample_rate": int(sample_rate),
                "samples": int(samples.size),
                "speech_seconds": float(state.speech_seconds),
                "trailing_silence_seconds": float(state.trailing_silence_seconds),
                "speech_started": bool(state.speech_started),
                "finished": bool(state.finished),
            },
        )
    except Exception as exc:
        result = DiagnosticResult(
            name="vad",
            status="error",
            details={"wav_path": str(source_path)},
            error=str(exc),
        )
    append_diagnostic_result(result, path=diagnostic_path)
    return result
