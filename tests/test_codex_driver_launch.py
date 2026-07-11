from __future__ import annotations

import unittest
from unittest.mock import patch

from voicecontrol.executor.app_driver import LaunchableAppDriver
from voicecontrol.executor.codex_driver import CodexDriver
from voicecontrol.executor.window_utils import Window, WindowError


class ExampleLaunchableDriver(LaunchableAppDriver):
    app_name = "Example App"


class LaunchableAppDriverTests(unittest.TestCase):
    def test_find_launches_missing_window_and_returns_it_when_it_appears(self) -> None:
        window = Window(hwnd=456, title="Example")
        driver = ExampleLaunchableDriver(
            window_title="Example",
            launch_command=r"C:\Apps\Example\Example.exe",
            launch_timeout=1.0,
            launch_poll_interval=0.1,
        )

        with (
            patch("voicecontrol.executor.app_driver.find_window", side_effect=[None, window]),
            patch("voicecontrol.executor.app_driver.subprocess.Popen") as popen,
            patch("voicecontrol.executor.app_driver.time.monotonic", side_effect=[0.0, 0.0]),
            patch("voicecontrol.executor.app_driver.time.sleep"),
        ):
            found = driver.find()

        self.assertEqual(found, window)
        popen.assert_called_once_with(r"C:\Apps\Example\Example.exe")


class CodexDriverLaunchTests(unittest.TestCase):
    def test_driver_uses_renamed_chatgpt_display_name(self) -> None:
        self.assertEqual(CodexDriver().app_name, "ChatGPT")

    def test_focus_launches_codex_when_window_is_missing(self) -> None:
        window = Window(hwnd=123, title="Codex")
        try:
            driver = CodexDriver(
                window_title="Codex",
                launch_command=r"C:\Apps\Codex\Codex.exe",
                launch_timeout=1.0,
                launch_poll_interval=0.1,
            )
        except TypeError as exc:
            self.fail(f"CodexDriver should accept launch settings: {exc}")

        with (
            patch("voicecontrol.executor.app_driver.find_window", side_effect=[None, window]),
            patch("voicecontrol.executor.app_driver.subprocess.Popen") as popen,
            patch("voicecontrol.executor.app_driver.focus_window") as focus_window,
            patch("voicecontrol.executor.app_driver.time.monotonic", side_effect=[0.0, 0.0]),
            patch("voicecontrol.executor.app_driver.time.sleep"),
        ):
            found = driver.focus()

        self.assertEqual(found, window)
        popen.assert_called_once_with(r"C:\Apps\Codex\Codex.exe")
        focus_window.assert_called_once()

    def test_focus_without_launch_command_keeps_window_not_found_error(self) -> None:
        try:
            driver = CodexDriver(window_title="Codex", launch_command="")
        except TypeError as exc:
            self.fail(f"CodexDriver should accept an empty launch command: {exc}")

        with patch("voicecontrol.executor.app_driver.find_window", return_value=None):
            with self.assertRaises(WindowError) as context:
                driver.focus()

        self.assertIn("window not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
