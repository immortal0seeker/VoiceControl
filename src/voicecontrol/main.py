"""VoiceControl CLI entry point.

Modes (mutually exclusive unless noted):
    --once      single fixed-duration recording, then transcribe (+ send)
    --default   hotkey loop: F9 start/stop, Esc quit
    --vad       hotkey loop with trailing-silence auto-stop
    --wake      always-on wake-word loop (foreground debug for the tray app)
    --no-send   transcribe only; skip the desktop executor (works with any mode)

This file handles input/triggering only; recording, STT, and sending live in
the pipeline and lower modules.
"""

from __future__ import annotations

import logging
import sys
import time

import keyboard

from voicecontrol.audio.device_manager import DeviceError
from voicecontrol.audio.recorder import RecordingError, StreamRecorder, record
from voicecontrol.config import settings
from voicecontrol.pipeline.orchestrator import PipelineResult, VoiceOrchestrator
from voicecontrol.stt.whisper_engine import TranscriptionError

logger = logging.getLogger(__name__)


def _force_utf8_stdout() -> None:
    """Make stdout/stderr UTF-8 so Chinese text prints correctly on Windows.

    The PowerShell console defaults to GBK, which mangles CJK output.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _print_result(result: PipelineResult) -> None:
    print("\n" + "=" * 40)
    if result.text:
        print(f"Recognized text:\n{result.text}")
    else:
        print("Recognized text is empty. Speak louder / closer to the mic.")

    if result.send_error:
        print(f"[send failed] {result.send_error}")
    elif result.sent:
        print("[sent to target app]")
    print("=" * 40)


def _wait_for_key(keys: set[str]) -> str:
    """Block until one of ``keys`` is pressed down; return the key name."""
    while True:
        event = keyboard.read_event(suppress=False)
        if event.event_type == keyboard.KEY_DOWN and event.name in keys:
            return event.name


def run_once(orchestrator: VoiceOrchestrator, seconds: float = settings.DEFAULT_RECORD_SECONDS) -> PipelineResult:
    """One fixed-duration record → transcribe → (send) cycle."""
    print(f"Recording {seconds:.0f}s — speak now...")
    audio = record(seconds=seconds)
    print("Transcribing...")
    return orchestrator.process_audio(audio)


def run_hotkey_loop(orchestrator: VoiceOrchestrator, use_vad: bool = False) -> None:
    """Hotkey-driven recording loop, then transcribe + send.

    With ``use_vad``, recording auto-stops on trailing silence; otherwise the
    user presses the record hotkey again to stop.
    """
    record_key = settings.RECORD_HOTKEY
    quit_key = settings.QUIT_HOTKEY

    stop_hint = "auto-stops on silence" if use_vad else f"[{record_key}] again to stop"
    print(
        f"\nReady. Press [{record_key}] to start recording ({stop_hint}), "
        f"[{quit_key}] to quit."
    )

    while True:
        key = _wait_for_key({record_key, quit_key})
        if key == quit_key:
            print("Exiting.")
            return

        if use_vad:
            print("\nRecording... (speak; auto-stops on silence)")
            audio = orchestrator.capture_until_silence()
        else:
            recorder = StreamRecorder()
            recorder.start()
            print(f"\nRecording... press [{record_key}] to stop.")
            time.sleep(0.4)  # debounce the start keypress before listening for stop
            _wait_for_key({record_key})
            audio = recorder.stop()

        print("Stopped. Transcribing...")
        result = orchestrator.process_audio(audio)
        _print_result(result)
        print(f"\nPress [{record_key}] to record again, [{quit_key}] to quit.")


def run_wake_foreground(orchestrator: VoiceOrchestrator) -> None:
    """Always-on wake-word loop in the foreground (Ctrl+C to stop)."""
    from voicecontrol.wake_word.detector import WakeWordDetector

    print("Loading wake word model...")
    detector = WakeWordDetector()
    print(
        f"\nListening. Say '{detector.model_name}' to start a command "
        f"(auto-stops on silence). Ctrl+C to quit."
    )

    def on_event(stage: str, result: PipelineResult | None = None) -> None:
        if stage == "wake":
            print("\n[wake] Heard it — speak your command...")
        elif stage == "done" and result is not None:
            _print_result(result)
            print(f"\nListening again. Say '{detector.model_name}'...")

    orchestrator.run_wake_loop(detector=detector, on_event=on_event)


def main() -> int:
    _force_utf8_stdout()
    # Foreground CLI mode: logging goes to the console (stderr) only, not to LOG_DIR.
    # Background tray mode writes logs to a daily file; see tray_app._configure_logging().
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    send_enabled = "--no-send" not in sys.argv
    use_wake = "--wake" in sys.argv
    use_hotkey = "--once" not in sys.argv
    use_vad = "--vad" in sys.argv

    print("Loading speech model...")
    orchestrator = VoiceOrchestrator(send_enabled=send_enabled)
    try:
        orchestrator.load()
        if use_wake:
            run_wake_foreground(orchestrator)
        elif use_hotkey:
            run_hotkey_loop(orchestrator, use_vad=use_vad)
        else:
            _print_result(run_once(orchestrator))
    except (DeviceError, RecordingError, TranscriptionError) as exc:
        print(f"ERROR: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
