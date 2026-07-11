from __future__ import annotations

import unittest
from unittest.mock import patch

from voicecontrol.config import settings
from voicecontrol.executor.chatgpt_driver import ChatGPTDriver
from voicecontrol.executor.window_utils import Window


class ChatGPTDriverTests(unittest.TestCase):
    def test_defaults_come_from_settings(self) -> None:
        driver = ChatGPTDriver()

        self.assertEqual(driver.app_name, "ChatGPT Classic")
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

    def test_composer_focus_uses_chatgpt_shortcut_without_clicking(self) -> None:
        window = Window(hwnd=789, title="ChatGPT")
        driver = ChatGPTDriver()

        with (
            patch.object(settings, "CLICK_COMPOSER_BEFORE_PASTE", True),
            patch("voicecontrol.executor.chatgpt_driver.keyboard.send") as send_key,
            patch("voicecontrol.executor.app_driver.click_in_window") as click,
            patch("voicecontrol.executor.chatgpt_driver.time.sleep") as sleep,
        ):
            driver._focus_composer(window)

        send_key.assert_called_once_with(ChatGPTDriver.COMPOSER_FOCUS_SHORTCUT)
        sleep.assert_called_once_with(settings.CLICK_SETTLE_DELAY)
        click.assert_not_called()

    def test_chatgpt_composer_focus_shortcut_matches_desktop_ui(self) -> None:
        self.assertEqual(ChatGPTDriver.COMPOSER_FOCUS_SHORTCUT, "ctrl+shift+l")


if __name__ == "__main__":
    unittest.main()
