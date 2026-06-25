from __future__ import annotations

import threading
import unittest
from unittest.mock import Mock, patch

import numpy as np

from voicecontrol import main
from voicecontrol.pipeline.orchestrator import PipelineResult


class _StopHotkey:
    def __init__(self, _key: str) -> None:
        self.stop_event = threading.Event()

    def __enter__(self) -> threading.Event:
        return self.stop_event

    def __exit__(self, *exc_info: object) -> None:
        return None


class HotkeyLoopManualStopTests(unittest.TestCase):
    def test_vad_mode_uses_second_record_hotkey_as_manual_stop(self) -> None:
        manual_stop = _StopHotkey("f9")
        orchestrator = Mock()
        orchestrator.capture_until_silence.return_value = np.array([[0.0]], dtype="float32")
        orchestrator.process_audio.return_value = PipelineResult(
            text="",
            wav_path=Mock(),
            sent=False,
        )

        with (
            patch.object(main, "_wait_for_key", side_effect=["f9", "esc"]),
            patch.object(main, "ManualStopHotkey", return_value=manual_stop) as stop_hotkey,
            patch("builtins.print"),
        ):
            main.run_hotkey_loop(orchestrator, use_vad=True)

        stop_hotkey.assert_called_once_with("f9")
        orchestrator.capture_until_silence.assert_called_once_with(
            stop_event=manual_stop.stop_event
        )


if __name__ == "__main__":
    unittest.main()
