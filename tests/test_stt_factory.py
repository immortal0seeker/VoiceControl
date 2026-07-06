from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from voicecontrol.stt.sensevoice_engine import SenseVoiceEngine
from voicecontrol.stt.whisper_engine import WhisperEngine


class STTFactoryTests(unittest.TestCase):
    def test_create_stt_engine_builds_whisper_engine_from_config(self) -> None:
        from voicecontrol.stt.factory import create_stt_engine

        config = {
            "stt": {
                "provider": "faster_whisper",
                "whisper_model_size": "medium",
                "whisper_device": "cpu",
                "whisper_compute_type": "int8",
                "whisper_language": "zh",
                "whisper_beam_size": 3,
                "whisper_vad_filter": False,
                "whisper_condition_on_previous_text": True,
            }
        }

        engine = create_stt_engine(config)

        self.assertIsInstance(engine, WhisperEngine)
        self.assertEqual(engine.model_size, "medium")
        self.assertEqual(engine.device, "cpu")
        self.assertEqual(engine.compute_type, "int8")
        self.assertEqual(engine.language, "zh")
        self.assertEqual(engine.beam_size, 3)
        self.assertFalse(engine.vad_filter)
        self.assertTrue(engine.condition_on_previous_text)

    def test_create_stt_engine_loads_config_when_not_supplied(self) -> None:
        from voicecontrol.stt.factory import create_stt_engine

        config = {
            "stt": {
                "provider": "faster_whisper",
                "whisper_model_size": "small",
                "whisper_device": "cuda",
                "whisper_compute_type": "float16",
                "whisper_language": None,
                "whisper_beam_size": 5,
                "whisper_vad_filter": True,
                "whisper_condition_on_previous_text": False,
            }
        }

        with patch("voicecontrol.stt.factory.load_config", return_value=config) as load_config:
            engine = create_stt_engine()

        load_config.assert_called_once_with()
        self.assertIsInstance(engine, WhisperEngine)
        self.assertEqual(engine.model_size, "small")

    def test_create_stt_engine_builds_sensevoice_engine_from_config(self) -> None:
        from voicecontrol.stt.factory import create_stt_engine

        config = {
            "stt": {
                "provider": "funasr_sensevoice",
                "sensevoice_model": "SenseVoiceSmall",
                "sensevoice_device": "cpu",
                "sensevoice_language": "zh",
            }
        }

        engine = create_stt_engine(config)

        self.assertIsInstance(engine, SenseVoiceEngine)
        self.assertEqual(engine.model, "SenseVoiceSmall")
        self.assertEqual(engine.device, "cpu")
        self.assertEqual(engine.language, "zh")

    def test_orchestrator_uses_stt_factory_by_default(self) -> None:
        engine = Mock()
        driver = Mock()

        with (
            patch("voicecontrol.pipeline.orchestrator.create_stt_engine", return_value=engine) as factory,
            patch("voicecontrol.pipeline.orchestrator.get_default_driver", return_value=driver),
        ):
            from voicecontrol.pipeline.orchestrator import VoiceOrchestrator

            orchestrator = VoiceOrchestrator()

        factory.assert_called_once_with()
        self.assertEqual(orchestrator.engine, engine)
        self.assertEqual(orchestrator.driver, driver)


if __name__ == "__main__":
    unittest.main()
