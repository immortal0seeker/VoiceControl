from __future__ import annotations

import threading
import unittest
from unittest.mock import Mock, patch

import numpy as np

from voicecontrol.pipeline.orchestrator import PipelineResult, VoiceOrchestrator


class _FakeRecorder:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def read_new(self) -> np.ndarray:
        return np.empty((0, 1), dtype="float32")

    def stop(self) -> np.ndarray:
        self.stopped = True
        return np.array([[0.0]], dtype="float32")


class _FailingDetector:
    def update(self, _audio: np.ndarray) -> object:
        raise AssertionError("detector should not run after manual stop is set")


class _StopHotkey:
    def __init__(self, _key: str) -> None:
        self.stop_event = threading.Event()

    def __enter__(self) -> threading.Event:
        return self.stop_event

    def __exit__(self, *exc_info: object) -> None:
        return None


class ManualRecordingStopTests(unittest.TestCase):
    def test_capture_until_silence_stops_when_external_event_is_set(self) -> None:
        recorder = _FakeRecorder()
        stop_event = threading.Event()
        stop_event.set()
        orchestrator = VoiceOrchestrator(engine=Mock(), driver=Mock())

        with (
            patch("voicecontrol.pipeline.orchestrator.StreamRecorder", return_value=recorder),
            patch("voicecontrol.pipeline.orchestrator.time.sleep"),
        ):
            audio = orchestrator.capture_until_silence(
                detector=_FailingDetector(),
                stop_event=stop_event,
            )

        self.assertTrue(recorder.started)
        self.assertTrue(recorder.stopped)
        self.assertEqual(audio.shape, (1, 1))

    def test_wake_loop_uses_manual_stop_hotkey_for_command_recording(self) -> None:
        orchestrator = VoiceOrchestrator(engine=Mock(), driver=Mock())
        detector = Mock()
        stop_event = threading.Event()
        manual_stop = _StopHotkey("f9")

        orchestrator._listen_for_wake = Mock(return_value=True)
        orchestrator.capture_until_silence = Mock(return_value=np.array([[0.0]], dtype="float32"))

        def process_audio(_audio: np.ndarray) -> PipelineResult:
            stop_event.set()
            return PipelineResult(text="", wav_path=Mock(), sent=False)

        orchestrator.process_audio = Mock(side_effect=process_audio)

        with patch(
            "voicecontrol.pipeline.orchestrator.ManualStopHotkey",
            return_value=manual_stop,
        ) as stop_hotkey:
            orchestrator.run_wake_loop(
                detector=detector,
                stop_event=stop_event,
                manual_stop_key="f9",
            )

        stop_hotkey.assert_called_once_with("f9")
        orchestrator.capture_until_silence.assert_called_once_with(
            stop_event=manual_stop.stop_event
        )


if __name__ == "__main__":
    unittest.main()
