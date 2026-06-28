from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from voicecontrol.events.status import StatusPublisher, StatusType
from voicecontrol.executor.window_utils import WindowError
from voicecontrol.pipeline.orchestrator import VoiceOrchestrator


class PipelineStatusEventTests(unittest.TestCase):
    def test_orchestrator_uses_default_driver_from_router(self) -> None:
        engine = Mock()
        driver = Mock()

        with patch("voicecontrol.pipeline.orchestrator.get_default_driver", return_value=driver):
            orchestrator = VoiceOrchestrator(engine=engine)

        self.assertEqual(orchestrator.driver, driver)

    def test_reload_driver_uses_fresh_config_factory(self) -> None:
        engine = Mock()
        old_driver = Mock()
        new_driver = Mock()
        new_driver.app_name = "Trae"
        config = {"executor": {"default_target": "trae"}}
        orchestrator = VoiceOrchestrator(engine=engine, driver=old_driver)

        with (
            patch("voicecontrol.config.manager.load_config", return_value=config) as load_config,
            patch(
                "voicecontrol.executor.router.create_driver_from_config",
                return_value=new_driver,
            ) as create_driver,
        ):
            orchestrator.reload_driver()

        load_config.assert_called_once_with()
        create_driver.assert_called_once_with(config)
        self.assertEqual(orchestrator.driver, new_driver)

    def test_process_audio_publishes_transcribing_sending_done(self) -> None:
        publisher = StatusPublisher()
        events: list[StatusType] = []
        publisher.subscribe(lambda event: events.append(event.type))

        engine = Mock()
        engine.transcribe_file.return_value = "打开项目"
        driver = Mock()
        driver.app_name = "Codex Desktop"
        orchestrator = VoiceOrchestrator(
            engine=engine,
            driver=driver,
            status_publisher=publisher,
        )

        with patch("voicecontrol.pipeline.orchestrator.save_wav", return_value=Path("command.wav")):
            result = orchestrator.process_audio(np.array([[0.0]], dtype="float32"))

        self.assertTrue(result.sent)
        self.assertEqual(
            events,
            [StatusType.TRANSCRIBING, StatusType.SENDING, StatusType.DONE],
        )

    def test_process_audio_publishes_error_when_sending_fails(self) -> None:
        publisher = StatusPublisher()
        events: list[StatusType] = []
        publisher.subscribe(lambda event: events.append(event.type))

        engine = Mock()
        engine.transcribe_file.return_value = "打开项目"
        driver = Mock()
        driver.app_name = "Codex Desktop"
        driver.send_prompt.side_effect = WindowError("missing window")
        orchestrator = VoiceOrchestrator(
            engine=engine,
            driver=driver,
            status_publisher=publisher,
        )

        with (
            patch("voicecontrol.pipeline.orchestrator.save_wav", return_value=Path("command.wav")),
            self.assertLogs("voicecontrol.pipeline.orchestrator", level="WARNING"),
        ):
            result = orchestrator.process_audio(np.array([[0.0]], dtype="float32"))

        self.assertFalse(result.sent)
        self.assertEqual(result.send_error, "missing window")
        self.assertEqual(
            events,
            [StatusType.TRANSCRIBING, StatusType.SENDING, StatusType.ERROR, StatusType.DONE],
        )


if __name__ == "__main__":
    unittest.main()
