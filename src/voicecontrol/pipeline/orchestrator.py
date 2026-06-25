"""Pipeline orchestration: tie audio → STT → executor together.

Orchestrates the lower modules; it does not reimplement recording, STT, or
window logic. The trigger (hotkey, wake word, etc.) lives in the entry point
and feeds recorded audio into ``process_audio``.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from voicecontrol.audio.recorder import MicFrameStream, StreamRecorder, save_wav
from voicecontrol.config import settings
from voicecontrol.executor.app_driver import AppDriver
from voicecontrol.executor.codex_driver import CodexDriver
from voicecontrol.executor.window_utils import WindowError
from voicecontrol.stt.whisper_engine import WhisperEngine
from voicecontrol.utils import feedback
from voicecontrol.utils.hotkeys import ManualStopHotkey
from voicecontrol.vad.silero_vad import EndpointDetector
from voicecontrol.wake_word.detector import WakeWordDetector

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Outcome of processing one recorded utterance."""

    text: str
    wav_path: Path
    sent: bool
    send_error: str | None = None


class VoiceOrchestrator:
    """Coordinates STT and the target-app driver for one utterance at a time."""

    def __init__(
        self,
        engine: WhisperEngine | None = None,
        driver: AppDriver | None = None,
        send_enabled: bool = True,
    ) -> None:
        self.engine = engine or WhisperEngine()
        self.driver = driver or CodexDriver()
        self.send_enabled = send_enabled

    def load(self) -> None:
        """Pre-load the STT model so the first utterance isn't slow."""
        self.engine.load()

    def capture_until_silence(
        self,
        detector: EndpointDetector | None = None,
        stop_event: threading.Event | None = None,
    ) -> np.ndarray:
        """Record from the mic and auto-stop after trailing silence.

        Stops when the endpoint detector reports the utterance finished, or on
        the safety caps (no speech started within ``VAD_START_TIMEOUT``; total
        time exceeds ``VAD_MAX_RECORD_SECONDS``).
        """
        detector = detector or EndpointDetector()
        recorder = StreamRecorder()
        recorder.start()
        start = time.monotonic()
        last_log = 0.0

        try:
            while True:
                time.sleep(settings.VAD_POLL_INTERVAL)
                elapsed = time.monotonic() - start
                if stop_event is not None and stop_event.is_set():
                    logger.info("Manual recording stop requested after %.1fs.", elapsed)
                    break
                # Feed only newly captured samples; the detector keeps running
                # totals, so each frame is scored once (O(n) over the utterance).
                state = detector.update(recorder.read_new().reshape(-1))

                if elapsed - last_log >= 1.0:
                    last_log = elapsed
                    logger.info(
                        "VAD: t=%.1fs speech=%.2fs trailing_silence=%.2fs started=%s",
                        elapsed, state.speech_seconds,
                        state.trailing_silence_seconds, state.speech_started,
                    )

                if state.finished:
                    logger.info(
                        "Endpoint: %.2fs speech, %.2fs trailing silence.",
                        state.speech_seconds, state.trailing_silence_seconds,
                    )
                    break
                if not state.speech_started and elapsed >= settings.VAD_START_TIMEOUT:
                    logger.info("No speech within %.1fs; stopping.", settings.VAD_START_TIMEOUT)
                    break
                if elapsed >= settings.VAD_MAX_RECORD_SECONDS:
                    logger.warning("Max record duration (%.0fs) reached.", settings.VAD_MAX_RECORD_SECONDS)
                    break
        finally:
            audio = recorder.stop()
        return audio

    def _listen_for_wake(
        self,
        detector: WakeWordDetector,
        stop_event: threading.Event,
        is_active: Callable[[], bool] | None,
    ) -> bool:
        """Block until the wake word is heard. Return False if stopped/paused-out.

        Opens (and closes) its own mic frame stream so the input device is free
        for the command recording that follows.
        """
        with MicFrameStream(settings.WAKE_FRAME_SAMPLES, dtype="int16") as mic:
            detector.reset()
            while not stop_event.is_set():
                if is_active is not None and not is_active():
                    return False  # paused: drop out so caller re-checks state
                frame = mic.read(timeout=0.2)
                if frame is None:
                    continue
                if detector.score(frame) >= detector.threshold:
                    return True
        return False

    def run_wake_loop(
        self,
        detector: WakeWordDetector | None = None,
        stop_event: threading.Event | None = None,
        is_active: Callable[[], bool] | None = None,
        on_event: Callable[[str, PipelineResult | None], None] | None = None,
        manual_stop_key: str | None = None,
    ) -> None:
        """Always-on loop: wake word → record command → transcribe → send.

        Blocks until ``stop_event`` is set. ``is_active`` lets a caller (e.g.
        the tray app) pause listening. ``on_event`` receives ("listening" |
        "wake" | "transcribing" | "done", result) for UI/status updates.
        """
        detector = detector or WakeWordDetector()
        stop_event = stop_event or threading.Event()

        def notify(stage: str, result: PipelineResult | None = None) -> None:
            if on_event is not None:
                on_event(stage, result)

        last_done_at: float = 0.0
        notify("listening")
        while not stop_event.is_set():
            # Cooldown measured from the end of the previous command, so a
            # trailing echo of one utterance can't immediately re-trigger.
            elapsed_since_done = time.monotonic() - last_done_at
            if elapsed_since_done < settings.WAKE_COOLDOWN:
                stop_event.wait(timeout=settings.WAKE_COOLDOWN - elapsed_since_done)
                if stop_event.is_set():
                    break

            woke = self._listen_for_wake(detector, stop_event, is_active)
            if not woke:
                continue  # stopped or paused; re-check loop condition

            logger.info("Wake word detected.")
            feedback.wake_cue()
            notify("wake")

            if manual_stop_key is None:
                audio = self.capture_until_silence()
            else:
                with ManualStopHotkey(manual_stop_key) as recording_stop_event:
                    audio = self.capture_until_silence(stop_event=recording_stop_event)
            notify("transcribing")
            result = self.process_audio(audio)
            feedback.done_cue()
            notify("done", result)
            last_done_at = time.monotonic()
            notify("listening")

    def process_audio(
        self,
        audio: np.ndarray,
        wav_path: str | Path | None = None,
    ) -> PipelineResult:
        """Save audio, transcribe, and (optionally) send the text to the app.

        ``wav_path`` defaults to a fresh timestamped file so each utterance is
        retained rather than overwriting a single recording.
        """
        if wav_path is None:
            wav_path = settings.new_recording_path()
        saved = save_wav(audio, wav_path)
        text = self.engine.transcribe_file(saved)

        sent = False
        send_error: str | None = None
        if self.send_enabled and text.strip():
            try:
                self.driver.send_prompt(text)
                sent = True
            except WindowError as exc:
                send_error = str(exc)
                logger.warning("Could not send to %s: %s", self.driver.app_name, exc)

        return PipelineResult(text=text, wav_path=saved, sent=sent, send_error=send_error)
