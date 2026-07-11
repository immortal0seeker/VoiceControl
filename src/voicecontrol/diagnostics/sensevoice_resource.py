"""SenseVoice resource benchmark diagnostics."""

from __future__ import annotations

import argparse
import ctypes
import json
import subprocess
import time
from pathlib import Path
from typing import Callable, Protocol

from voicecontrol.config import settings
from voicecontrol.diagnostics.store import DiagnosticResult, append_diagnostic_result
from voicecontrol.diagnostics.stt_model_compare import latest_recording_path
from voicecontrol.stt.engine import TranscriptionResult
from voicecontrol.stt.sensevoice_engine import SenseVoiceEngine


class SenseVoiceBenchmarkEngine(Protocol):
    """Subset of SenseVoiceEngine needed by the benchmark."""

    engine_name: str
    model: str
    device: str
    language: str | None

    def transcribe_file(self, path: Path) -> TranscriptionResult:
        """Transcribe ``path`` and return normalized metadata."""


EngineFactory = Callable[..., SenseVoiceBenchmarkEngine]
FloatReader = Callable[[], float]
IntReader = Callable[[], int | None]


def run_sensevoice_resource_benchmark(
    audio_path: str | Path | None = None,
    *,
    model: str = settings.SENSEVOICE_MODEL,
    device: str = settings.SENSEVOICE_DEVICE,
    language: str | None = settings.SENSEVOICE_LANGUAGE,
    diagnostic_path: str | Path | None = None,
    engine_factory: EngineFactory = SenseVoiceEngine,
    perf_counter: FloatReader = time.perf_counter,
    rss_reader: IntReader = None,  # type: ignore[assignment]
    gpu_memory_reader: IntReader = None,  # type: ignore[assignment]
) -> DiagnosticResult:
    """Benchmark SenseVoice cold and warm transcription resource usage."""
    rss_reader = current_process_rss_bytes if rss_reader is None else rss_reader
    gpu_memory_reader = nvidia_smi_memory_used_mb if gpu_memory_reader is None else gpu_memory_reader

    selected_audio_path = Path(audio_path) if audio_path is not None else latest_recording_path()
    if selected_audio_path is None:
        result = DiagnosticResult(
            name="sensevoice_resource_benchmark",
            status="error",
            details=_base_details(model, device, language, None),
            error="No WAV recording found for SenseVoice resource benchmark.",
        )
        append_diagnostic_result(result, path=diagnostic_path)
        return result

    if not selected_audio_path.is_file():
        result = DiagnosticResult(
            name="sensevoice_resource_benchmark",
            status="error",
            details=_base_details(model, device, language, selected_audio_path),
            error=f"Audio file not found: {selected_audio_path}",
        )
        append_diagnostic_result(result, path=diagnostic_path)
        return result

    details = _base_details(model, device, language, selected_audio_path)
    try:
        rss_before = rss_reader()
        gpu_before = gpu_memory_reader()
        engine = engine_factory(model=model, device=device, language=language)

        cold_started_at = perf_counter()
        cold_result = engine.transcribe_file(selected_audio_path)
        cold_seconds = perf_counter() - cold_started_at
        rss_after_cold = rss_reader()
        gpu_after_cold = gpu_memory_reader()

        warm_started_at = perf_counter()
        warm_result = engine.transcribe_file(selected_audio_path)
        warm_seconds = perf_counter() - warm_started_at
        rss_after_warm = rss_reader()
        gpu_after_warm = gpu_memory_reader()
    except Exception as exc:
        details["process_rss_bytes"] = {"before": _safe_read(rss_reader)}
        details["gpu_memory_mb"] = _safe_read(gpu_memory_reader)
        result = DiagnosticResult(
            name="sensevoice_resource_benchmark",
            status="error",
            details=details,
            error=str(exc),
        )
        append_diagnostic_result(result, path=diagnostic_path)
        return result

    details.update(
        {
            "provider": cold_result.engine,
            "model": cold_result.model,
            "cold_load_transcribe_seconds": round(cold_seconds, 3),
            "warm_transcribe_seconds": round(warm_seconds, 3),
            "process_rss_bytes": {
                "before": rss_before,
                "after_cold": rss_after_cold,
                "after_warm": rss_after_warm,
                "cold_delta": _delta(rss_before, rss_after_cold),
                "warm_delta": _delta(rss_after_cold, rss_after_warm),
                "total_delta": _delta(rss_before, rss_after_warm),
            },
            "gpu_memory_mb": _gpu_memory_details(gpu_before, gpu_after_cold, gpu_after_warm),
            "cold_text": cold_result.text,
            "warm_text": warm_result.text,
            "language": cold_result.language,
        }
    )
    result = DiagnosticResult(
        name="sensevoice_resource_benchmark",
        status="ok",
        details=details,
    )
    append_diagnostic_result(result, path=diagnostic_path)
    return result


def current_process_rss_bytes() -> int | None:
    """Return current process RSS in bytes on Windows, or None if unavailable."""
    try:
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(ProcessMemoryCounters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.argtypes = []
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        ok = psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(),
            ctypes.byref(counters),
            counters.cb,
        )
        if not ok:
            return None
        return int(counters.WorkingSetSize)
    except Exception:
        return None


def nvidia_smi_memory_used_mb() -> int | None:
    """Return summed NVIDIA GPU memory usage in MiB, or None when unavailable."""
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None

    values: list[int] = []
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            values.append(int(stripped))
        except ValueError:
            return None
    if not values:
        return None
    return sum(values)


def _base_details(
    model: str,
    device: str,
    language: str | None,
    audio_path: Path | None,
) -> dict[str, object]:
    return {
        "provider": "funasr_sensevoice",
        "model": model,
        "device": device,
        "language": language,
        "audio_path": str(audio_path) if audio_path is not None else None,
    }


def _gpu_memory_details(
    before: int | None,
    after_cold: int | None,
    after_warm: int | None,
) -> dict[str, int | None] | None:
    if before is None and after_cold is None and after_warm is None:
        return None
    return {
        "before": before,
        "after_cold": after_cold,
        "after_warm": after_warm,
        "cold_delta": _delta(before, after_cold),
        "warm_delta": _delta(after_cold, after_warm),
        "total_delta": _delta(before, after_warm),
    }


def _delta(before: int | None, after: int | None) -> int | None:
    if before is None or after is None:
        return None
    return after - before


def _safe_read(reader: IntReader) -> int | None:
    try:
        return reader()
    except Exception:
        return None


def main() -> None:
    """Run the SenseVoice resource benchmark from PowerShell."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", type=Path, default=None, help="WAV file to transcribe.")
    parser.add_argument("--model", default=settings.SENSEVOICE_MODEL)
    parser.add_argument("--device", default=settings.SENSEVOICE_DEVICE)
    parser.add_argument("--language", default=settings.SENSEVOICE_LANGUAGE)
    args = parser.parse_args()

    result = run_sensevoice_resource_benchmark(
        args.audio,
        model=args.model,
        device=args.device,
        language=args.language,
    )
    print(json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
