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

    def test_default_composer_focus_clicks_one_candidate_position(self) -> None:
        window = Window(hwnd=987, title="Cursor")
        driver = CursorDriver()

        with (
            patch.object(settings, "CLICK_COMPOSER_BEFORE_PASTE", True),
            patch.object(settings, "COMPOSER_CLICK_REL_X", 0.5),
            patch.object(settings, "COMPOSER_CLICK_REL_Y", 0.9),
            patch("voicecontrol.executor.cursor_driver.click_in_window") as click,
        ):
            driver._focus_composer(window)

        click.assert_called_once_with(
            window,
            0.5,
            0.9,
            settle_delay=settings.CLICK_SETTLE_DELAY,
        )


if __name__ == "__main__":
    unittest.main()
