from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from voicecontrol.wake_word.detector import WakeWordDetector
from voicecontrol.wake_word.models import (
    available_wake_word_models,
    resolve_wake_word_model,
)


class WakeWordModelRegistryTests(unittest.TestCase):
    def test_available_models_include_builtin_and_bundled_custom_model(self) -> None:
        self.assertIn("hey_jarvis", available_wake_word_models())
        self.assertIn("world_activate", available_wake_word_models())

    def test_resolve_builtin_model_keeps_pretrained_name(self) -> None:
        spec = resolve_wake_word_model("hey_jarvis")

        self.assertEqual(spec.name, "hey_jarvis")
        self.assertEqual(spec.model_arg, "hey_jarvis")
        self.assertEqual(spec.score_key, "hey_jarvis")

    def test_resolve_bundled_custom_model_uses_onnx_path_and_stem_score_key(self) -> None:
        spec = resolve_wake_word_model("world_activate")

        self.assertEqual(spec.name, "world_activate")
        self.assertEqual(Path(spec.model_arg).name, "world_activate.onnx")
        self.assertEqual(spec.score_key, "world_activate")


class WakeWordDetectorModelTests(unittest.TestCase):
    def test_detector_loads_bundled_custom_model_path_and_scores_by_stem(self) -> None:
        model = Mock()
        model.predict.return_value = {"world_activate": 0.75}

        with patch("voicecontrol.wake_word.detector.Model", return_value=model) as model_class:
            detector = WakeWordDetector(model_name="world_activate", threshold=0.5)

        model_arg = model_class.call_args.kwargs["wakeword_models"][0]
        self.assertEqual(Path(model_arg).name, "world_activate.onnx")
        self.assertEqual(detector.score(np.zeros(1280, dtype=np.int16)), 0.75)


if __name__ == "__main__":
    unittest.main()
