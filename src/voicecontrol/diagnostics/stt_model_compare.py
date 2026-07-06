"""Compare local STT models on the same existing audio file."""

from __future__ import annotations

from copy import deepcopy
import time
from pathlib import Path

from voicecontrol.config import settings
from voicecontrol.config.manager import DEFAULT_CONFIG
from voicecontrol.diagnostics.store import DiagnosticResult, append_diagnostic_result
from voicecontrol.stt.factory import create_stt_engine


DEFAULT_COMPARE_MODELS: tuple[str, ...] = ("small", "medium", "sensevoice_small")


def latest_recording_path(recordings_dir: str | Path | None = None) -> Path | None:
    """Return the newest WAV recording, or None when no recording exists."""
    directory = Path(recordings_dir) if recordings_dir is not None else settings.RECORDINGS_DIR
    if not directory.exists():
        return None
    candidates = [path for path in directory.glob("*.wav") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def run_stt_model_compare(
    audio_path: str | Path | None = None,
    *,
    models: tuple[str, ...] = DEFAULT_COMPARE_MODELS,
    diagnostic_path: str | Path | None = None,
) -> DiagnosticResult:
    """Transcribe one local audio file with each model and record the comparison."""
    selected_audio_path = Path(audio_path) if audio_path is not None else latest_recording_path()
    if selected_audio_path is None:
        result = DiagnosticResult(
            name="stt_model_compare",
            status="error",
            details={},
            error="No WAV recording found for STT comparison.",
        )
        append_diagnostic_result(result, path=diagnostic_path)
        return result
    if not selected_audio_path.is_file():
        result = DiagnosticResult(
            name="stt_model_compare",
            status="error",
            details={"audio_path": str(selected_audio_path)},
            error=f"Audio file not found: {selected_audio_path}",
        )
        append_diagnostic_result(result, path=diagnostic_path)
        return result

    model_details: dict[str, dict[str, object]] = {}
    status = "ok"
    error: str | None = None
    for model in models:
        started_at = time.perf_counter()
        try:
            engine = create_stt_engine(_config_for_compare_model(model))
            transcription = engine.transcribe_file(selected_audio_path)
            elapsed = transcription.duration_seconds
            if elapsed is None:
                elapsed = time.perf_counter() - started_at
            model_details[model] = {
                "text": transcription.text,
                "engine": transcription.engine,
                "model": transcription.model,
                "duration_seconds": round(elapsed, 3),
                "language": transcription.language,
                "language_probability": transcription.language_probability,
            }
        except Exception as exc:
            status = "error"
            error = str(exc)
            model_details[model] = {"error": str(exc)}

    result = DiagnosticResult(
        name="stt_model_compare",
        status=status,
        details={
            "audio_path": str(selected_audio_path),
            "models": model_details,
        },
        error=error,
    )
    append_diagnostic_result(result, path=diagnostic_path)
    return result


def _config_for_compare_model(model: str) -> dict[str, object]:
    config = deepcopy(DEFAULT_CONFIG)
    stt_config = config["stt"]
    if model in {"small", "medium"}:
        stt_config["provider"] = "faster_whisper"
        stt_config["whisper_model_size"] = model
        stt_config["whisper_model_profile"] = (
            "balanced_small" if model == "small" else "accuracy_medium"
        )
        return config

    if model == "sensevoice_small":
        stt_config["provider"] = "funasr_sensevoice"
        stt_config["sensevoice_model"] = "SenseVoiceSmall"
        stt_config["sensevoice_device"] = settings.SENSEVOICE_DEVICE
        stt_config["sensevoice_language"] = settings.SENSEVOICE_LANGUAGE
        return config

    raise ValueError(
        f"Unknown STT compare model {model!r}; expected small, medium, or sensevoice_small"
    )
