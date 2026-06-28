from __future__ import annotations

import unittest
from unittest.mock import patch

from voicecontrol.config import settings
from voicecontrol.executor.chatgpt_driver import ChatGPTDriver
from voicecontrol.executor.window_utils import Window


class ChatGPTDriverTests(unittest.TestCase):
    def test_defaults_come_from_settings(self) -> None:
        driver = ChatGPTDriver()

        self.assertEqual(driver.app_name, "ChatGPT Desktop")
        self.assertEqual(driver.window_title, settings.CHATGPT_WINDOW_TITLE)
        self.assertEqual(driver.launch_command, settings.CHATGPT_LAUNCH_COMMAND)
        self.assertEqual(driver.launch_timeout, settings.CHATGPT_LAUNCH_TIMEOUT)
        self.assertEqual(driver.launch_poll_interval, settings.CHATGPT_LAUNCH_POLL_INTERVAL)

    def test_focus_launches_chatgpt_when_window_is_missing(self) -> None:
        window = Window(hwnd=789, title="ChatGPT")
        driver = ChatGPTDriver(
            window_title="ChatGPT",
            launch_command=r"C:\Apps\ChatGPT\ChatGPT.exe",
            launch_timeout=1.0,
            launch_poll_interval=0.1,
        )

        with (
            patch("voicecontrol.executor.app_driver.find_window", side_effect=[None, window]),
            patch("voicecontrol.executor.app_driver.subprocess.Popen") as popen,
            patch("voicecontrol.executor.app_driver.focus_window") as focus_window,
            patch("voicecontrol.executor.app_driver.time.monotonic", side_effect=[0.0, 0.0]),
            patch("voicecontrol.executor.app_driver.time.sleep"),
        ):
            found = driver.focus()

        self.assertEqual(found, window)
        popen.assert_called_once_with(r"C:\Apps\ChatGPT\ChatGPT.exe")
        focus_window.assert_called_once()


if __name__ == "__main__":
    unittest.main()
