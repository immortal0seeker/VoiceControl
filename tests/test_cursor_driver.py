from __future__ import annotations

import unittest
from unittest.mock import patch

from voicecontrol.config import settings
from voicecontrol.executor.cursor_driver import CursorDriver
from voicecontrol.executor.window_utils import Window


class CursorDriverTests(unittest.TestCase):
    def test_defaults_come_from_settings(self) -> None:
        driver = CursorDriver()

        self.assertEqual(driver.app_name, "Cursor")
        self.assertEqual(driver.window_title, settings.CURSOR_WINDOW_TITLE)
        self.assertEqual(driver.launch_command, settings.CURSOR_LAUNCH_COMMAND)
        self.assertEqual(driver.launch_timeout, settings.CURSOR_LAUNCH_TIMEOUT)
        self.assertEqual(driver.launch_poll_interval, settings.CURSOR_LAUNCH_POLL_INTERVAL)
        self.assertFalse(hasattr(driver, "composer_click_rel_x"))
        self.assertFalse(hasattr(driver, "composer_click_rel_y"))

    def test_focus_launches_cursor_when_window_is_missing(self) -> None:
        window = Window(hwnd=987, title="Cursor")
        driver = CursorDriver(
            window_title="Cursor",
            launch_command=r"C:\Apps\Cursor\Cursor.exe",
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
        popen.assert_called_once_with(r"C:\Apps\Cursor\Cursor.exe")
        focus_window.assert_called_once()

    def test_composer_focus_uses_cursor_shortcut_without_clicking(self) -> None:
        window = Window(hwnd=987, title="Cursor")
        driver = CursorDriver()

        with (
            patch.object(settings, "CLICK_COMPOSER_BEFORE_PASTE", True),
            patch("voicecontrol.executor.cursor_driver.keyboard.send") as send_key,
            patch("voicecontrol.executor.app_driver.click_in_window") as click,
            patch("voicecontrol.executor.cursor_driver.time.sleep") as sleep,
        ):
            driver._focus_composer(window)

        send_key.assert_called_once_with(CursorDriver.AI_SIDEBAR_SHORTCUT)
        sleep.assert_called_once_with(settings.CLICK_SETTLE_DELAY)
        click.assert_not_called()

    def test_cursor_chat_focus_shortcut_matches_cursor_ui(self) -> None:
        self.assertEqual(CursorDriver.AI_SIDEBAR_SHORTCUT, "ctrl+shift+l")


if __name__ == "__main__":
    unittest.main()
