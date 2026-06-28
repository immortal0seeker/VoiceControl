from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from voicecontrol.executor.window_utils import WindowError
from voicecontrol.history.resend import ResendError, resend_last_command
from voicecontrol.history.store import CommandHistoryRecord, append_command_history, latest_command_with_text


class ResendLastCommandTests(unittest.TestCase):
    def test_resend_last_command_uses_default_driver_from_router(self) -> None:
        driver = Mock()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"
            append_command_history(CommandHistoryRecord(text="上一条命令", wav_path=Path("old.wav"), sent=True), path=path)

            with patch("voicecontrol.history.resend.get_default_driver", return_value=driver):
                resend_last_command(history_path=path)

        driver.send_prompt.assert_called_once_with("上一条命令")

    def test_latest_command_with_text_skips_empty_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"
            append_command_history(
                CommandHistoryRecord(text="", wav_path=Path("first.wav"), sent=False, error="empty"),
                path=path,
            )
            append_command_history(
                CommandHistoryRecord(text="打开项目", wav_path=Path("second.wav"), sent=True),
                path=path,
            )

            record = latest_command_with_text(path=path)

        self.assertIsNotNone(record)
        self.assertEqual(record.text, "打开项目")
        self.assertEqual(record.wav_path, Path("second.wav"))

    def test_resend_last_command_sends_latest_text_and_records_result(self) -> None:
        driver = Mock()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"
            append_command_history(CommandHistoryRecord(text="上一条命令", wav_path=Path("old.wav"), sent=True), path=path)

            result = resend_last_command(driver=driver, history_path=path)

            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        driver.send_prompt.assert_called_once_with("上一条命令")
        self.assertTrue(result.sent)
        self.assertEqual(result.text, "上一条命令")
        self.assertEqual(rows[-1]["text"], "上一条命令")
        self.assertTrue(rows[-1]["sent"])
        self.assertIsNone(rows[-1]["send_error"])

    def test_resend_last_command_records_send_failure(self) -> None:
        driver = Mock()
        driver.send_prompt.side_effect = WindowError("missing window")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"
            append_command_history(CommandHistoryRecord(text="上一条命令", wav_path=Path("old.wav"), sent=True), path=path)

            with self.assertLogs("voicecontrol.history.resend", level="WARNING"):
                result = resend_last_command(driver=driver, history_path=path)

            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertFalse(result.sent)
        self.assertEqual(result.send_error, "missing window")
        self.assertEqual(rows[-1]["send_error"], "missing window")

    def test_resend_last_command_raises_when_history_has_no_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.jsonl"

            with self.assertRaises(ResendError):
                resend_last_command(driver=Mock(), history_path=path)


if __name__ == "__main__":
    unittest.main()
