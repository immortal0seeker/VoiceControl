from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from voicecontrol.control.commands import (
    PAUSE_LISTENING,
    RELOAD_EXECUTOR,
    RESUME_LISTENING,
    START_RECORDING,
    STOP_RECORDING,
    read_control_command,
    read_control_response,
    write_control_command,
    write_control_response,
)


class ControlCommandTests(unittest.TestCase):
    def test_write_and_consume_control_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "command.json"

            write_control_command(START_RECORDING, path)

            self.assertEqual(read_control_command(path), START_RECORDING)
            self.assertIsNone(read_control_command(path))

    def test_unknown_command_is_ignored_and_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "command.json"
            path.write_text('{"command": "dance"}', encoding="utf-8")

            self.assertIsNone(read_control_command(path))
            self.assertFalse(path.exists())

    def test_stop_recording_command_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "command.json"

            write_control_command(STOP_RECORDING, path)

            self.assertEqual(read_control_command(path), STOP_RECORDING)

    def test_pause_and_resume_listening_commands_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "command.json"

            write_control_command(PAUSE_LISTENING, path)
            self.assertEqual(read_control_command(path), PAUSE_LISTENING)

            write_control_command(RESUME_LISTENING, path)
            self.assertEqual(read_control_command(path), RESUME_LISTENING)

    def test_stale_command_is_ignored_and_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "command.json"
            path.write_text(
                '{"command": "start_recording", "created_at": 1}',
                encoding="utf-8",
            )

            self.assertIsNone(read_control_command(path, max_age_seconds=0.01))
            self.assertFalse(path.exists())

    def test_write_and_read_control_response(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "response.json"

            write_control_response(RELOAD_EXECUTOR, "ok", "Executor reloaded", path)
            response = read_control_response(path)

        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response["command"], RELOAD_EXECUTOR)
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["message"], "Executor reloaded")


if __name__ == "__main__":
    unittest.main()
