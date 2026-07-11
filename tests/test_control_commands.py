from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
    def test_write_control_command_writes_a_sibling_temp_file_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "command.json"
            written_paths: list[Path] = []
            original_write_text = Path.write_text

            def observe_write_text(file_path: Path, *args: object, **kwargs: object) -> int:
                written_paths.append(file_path)
                return original_write_text(file_path, *args, **kwargs)

            with patch.object(Path, "write_text", autospec=True, side_effect=observe_write_text):
                write_control_command(START_RECORDING, path)

            self.assertTrue(written_paths)
            self.assertNotEqual(written_paths[0], path)
            self.assertEqual(written_paths[0].parent, path.parent)
            self.assertEqual(read_control_command(path), START_RECORDING)

    def test_write_control_response_writes_a_sibling_temp_file_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "response.json"
            written_paths: list[Path] = []
            original_write_text = Path.write_text

            def observe_write_text(file_path: Path, *args: object, **kwargs: object) -> int:
                written_paths.append(file_path)
                return original_write_text(file_path, *args, **kwargs)

            with patch.object(Path, "write_text", autospec=True, side_effect=observe_write_text):
                write_control_response(RELOAD_EXECUTOR, "ok", "Executor reloaded", path)

            self.assertTrue(written_paths)
            self.assertNotEqual(written_paths[0], path)
            self.assertEqual(written_paths[0].parent, path.parent)
            response = read_control_response(path)
            self.assertIsNotNone(response)
            assert response is not None
            self.assertEqual(response["status"], "ok")

    def test_write_and_consume_control_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "command.json"

            write_control_command(START_RECORDING, path)

            self.assertEqual(read_control_command(path), START_RECORDING)
            self.assertIsNone(read_control_command(path))

    def test_read_control_command_does_not_delete_a_newly_published_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "command.json"
            write_control_command(START_RECORDING, path)
            original_read_text = Path.read_text
            published_replacement = False

            def publish_during_read(file_path: Path, *args: object, **kwargs: object) -> str:
                nonlocal published_replacement
                content = original_read_text(file_path, *args, **kwargs)
                if not published_replacement:
                    published_replacement = True
                    write_control_command(STOP_RECORDING, path)
                return content

            with patch.object(Path, "read_text", autospec=True, side_effect=publish_during_read):
                self.assertEqual(read_control_command(path), START_RECORDING)

            self.assertEqual(read_control_command(path), STOP_RECORDING)

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
