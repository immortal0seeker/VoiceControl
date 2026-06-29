from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from voicecontrol.history.store import CommandHistoryRecord, append_command_history
from voicecontrol.pipeline.orchestrator import VoiceOrchestrator
from voicecontrol.stt.engine import TranscriptionResult


class CommandHistoryStoreTests(unittest.TestCase):
    def test_append_command_history_writes_json_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"
            record = CommandHistoryRecord(
                text="打开项目",
                wav_path=Path("audio_files/recordings/command.wav"),
                sent=True,
                send_error=None,
            )

            append_command_history(record, path=path)

            lines = path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 1)
        data = json.loads(lines[0])
        self.assertEqual(data["text"], "打开项目")
        self.assertEqual(data["wav_path"], "audio_files/recordings/command.wav")
        self.assertTrue(data["sent"])
        self.assertIsNone(data["send_error"])
        self.assertIsNone(data["error"])
        self.assertIn("created_at", data)

    def test_append_command_history_writes_stt_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"
            record = CommandHistoryRecord(
                text="打开项目",
                raw_text="打开项目",
                wav_path=Path("audio_files/recordings/command.wav"),
                sent=True,
                stt_engine="faster_whisper",
                stt_model="small",
                stt_language="zh",
                stt_language_probability=0.93,
            )

            append_command_history(record, path=path)
            data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["raw_text"], "打开项目")
        self.assertEqual(data["stt_engine"], "faster_whisper")
        self.assertEqual(data["stt_model"], "small")
        self.assertEqual(data["stt_language"], "zh")
        self.assertEqual(data["stt_language_probability"], 0.93)

    def test_process_audio_records_command_history(self) -> None:
        engine = Mock()
        engine.transcribe_file.return_value = TranscriptionResult(
            text="打开项目",
            engine="faster_whisper",
            model="small",
            language="zh",
            language_probability=0.93,
        )
        driver = Mock()
        driver.app_name = "Codex Desktop"
        orchestrator = VoiceOrchestrator(engine=engine, driver=driver)

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("voicecontrol.pipeline.orchestrator.save_wav", return_value=Path("command.wav")),
            patch(
                "voicecontrol.pipeline.orchestrator.settings.COMMAND_HISTORY_PATH",
                Path(temp_dir) / "history.jsonl",
            ),
        ):
            orchestrator.process_audio(np.array([[0.0]], dtype="float32"))
            data = json.loads((Path(temp_dir) / "history.jsonl").read_text(encoding="utf-8"))

        self.assertEqual(data["text"], "打开项目")
        self.assertEqual(data["wav_path"], "command.wav")
        self.assertTrue(data["sent"])
        self.assertIsNone(data["send_error"])
        self.assertEqual(data["raw_text"], "打开项目")
        self.assertEqual(data["stt_engine"], "faster_whisper")
        self.assertEqual(data["stt_model"], "small")
        self.assertEqual(data["stt_language"], "zh")
        self.assertEqual(data["stt_language_probability"], 0.93)

    def test_process_audio_records_transcription_error_history(self) -> None:
        engine = Mock()
        engine.transcribe_file.side_effect = RuntimeError("model failed")
        driver = Mock()
        driver.app_name = "Codex Desktop"
        orchestrator = VoiceOrchestrator(engine=engine, driver=driver)

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("voicecontrol.pipeline.orchestrator.save_wav", return_value=Path("command.wav")),
            patch(
                "voicecontrol.pipeline.orchestrator.settings.COMMAND_HISTORY_PATH",
                Path(temp_dir) / "history.jsonl",
            ),
        ):
            with self.assertRaises(RuntimeError):
                orchestrator.process_audio(np.array([[0.0]], dtype="float32"))
            data = json.loads((Path(temp_dir) / "history.jsonl").read_text(encoding="utf-8"))

        self.assertEqual(data["text"], "")
        self.assertEqual(data["wav_path"], "command.wav")
        self.assertFalse(data["sent"])
        self.assertEqual(data["error"], "model failed")


if __name__ == "__main__":
    unittest.main()
