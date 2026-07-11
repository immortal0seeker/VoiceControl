from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from voicecontrol.stt.whisper_engine import TranscriptionError, WhisperEngine


class WhisperEngineLoadTests(unittest.TestCase):
    def test_cuda_load_falls_back_to_cpu_int8(self) -> None:
        cpu_model = Mock()
        with patch(
            "voicecontrol.stt.whisper_engine.WhisperModel",
            side_effect=[RuntimeError("cuda unavailable"), cpu_model],
        ) as model_class:
            engine = WhisperEngine(device="cuda", compute_type="float16")
            engine.load()

        self.assertIs(engine._model, cpu_model)
        self.assertEqual(engine.device, "cpu")
        self.assertEqual(engine.compute_type, "int8")
        self.assertEqual(model_class.call_count, 2)

    def test_cpu_fallback_failure_is_wrapped_as_transcription_error(self) -> None:
        with patch(
            "voicecontrol.stt.whisper_engine.WhisperModel",
            side_effect=[RuntimeError("cuda failed"), RuntimeError("cpu failed")],
        ):
            engine = WhisperEngine(device="cuda", compute_type="float16")

            with self.assertRaisesRegex(TranscriptionError, "CPU fallback also failed"):
                engine.load()


if __name__ == "__main__":
    unittest.main()
