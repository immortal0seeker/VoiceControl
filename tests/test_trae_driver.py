from __future__ import annotations

import unittest
from unittest.mock import call, patch

from voicecontrol.config import settings
from voicecontrol.executor.trae_driver import TraeDriver
from voicecontrol.executor.window_utils import Window


class TraeDriverTests(unittest.TestCase):
    def test_neutral_click_shortcut_strategy_defocuses_then_uses_shortcut_without_composer_click(self) -> None:
        window = Window(hwnd=456, title="Trae")
        driver = TraeDriver(
            neutral_click_rel_x=0.5,
            neutral_click_rel_y=0.985,
            ai_sidebar_shortcut="ctrl+u",
        )

        with (
            patch.object(settings, "CLICK_COMPOSER_BEFORE_PASTE", True),
            patch("voicecontrol.executor.trae_driver.click_in_window") as click,
            patch("voicecontrol.executor.trae_driver.keyboard.send") as send_key,
            patch("voicecontrol.executor.trae_driver.time.sleep") as sleep,
        ):
            driver._focus_composer(window)

        self.assertEqual(
            click.call_args_list,
            [
                call(window, 0.5, 0.985, settle_delay=settings.CLICK_SETTLE_DELAY),
            ],
        )
        send_key.assert_called_once_with("ctrl+u")
        sleep.assert_called_once_with(settings.CLICK_SETTLE_DELAY)

    def test_default_trae_shortcut_matches_ui_documentation(self) -> None:
        self.assertEqual(TraeDriver.AI_SIDEBAR_SHORTCUT, "ctrl+u")


if __name__ == "__main__":
    unittest.main()
