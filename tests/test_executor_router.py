from __future__ import annotations

import unittest

from voicecontrol.executor.chatgpt_driver import ChatGPTDriver
from voicecontrol.executor.codex_driver import CodexDriver
from voicecontrol.executor.cursor_driver import CursorDriver
from voicecontrol.executor import router
from voicecontrol.executor.router import create_driver
from voicecontrol.executor.trae_driver import TraeDriver


class ExecutorRouterTests(unittest.TestCase):
    def test_create_driver_returns_requested_target_driver(self) -> None:
        self.assertIsInstance(create_driver("codex"), CodexDriver)
        self.assertIsInstance(create_driver("chatgpt"), ChatGPTDriver)
        self.assertIsInstance(create_driver("cursor"), CursorDriver)
        self.assertIsInstance(create_driver("trae"), TraeDriver)

    def test_create_driver_from_config_uses_fresh_values(self) -> None:
        config = {
            "executor": {
                "default_target": "trae",
                "trae_window_title": "Fresh Trae",
                "trae_launch_command": r"C:\Apps\Trae\Trae.exe",
                "trae_launch_timeout": 7.0,
                "trae_launch_poll_interval": 0.25,
                "trae_neutral_click_rel_x": 0.51,
                "trae_neutral_click_rel_y": 0.98,
                "trae_ai_sidebar_shortcut": "ctrl+u",
            }
        }

        driver = router.create_driver_from_config(config)

        self.assertIsInstance(driver, TraeDriver)
        self.assertEqual(driver.window_title, "Fresh Trae")
        self.assertEqual(driver.launch_command, r"C:\Apps\Trae\Trae.exe")
        self.assertEqual(driver.launch_timeout, 7.0)
        self.assertEqual(driver.launch_poll_interval, 0.25)
        self.assertFalse(hasattr(driver, "composer_click_rel_x"))
        self.assertFalse(hasattr(driver, "composer_click_rel_y"))
        self.assertFalse(hasattr(driver, "focus_strategy"))
        self.assertEqual(driver.neutral_click_rel_x, 0.51)
        self.assertEqual(driver.neutral_click_rel_y, 0.98)
        self.assertEqual(driver.ai_sidebar_shortcut, "ctrl+u")

    def test_create_cursor_driver_from_config_ignores_cursor_composer_position(self) -> None:
        config = {
            "executor": {
                "default_target": "cursor",
                "cursor_window_title": "Fresh Cursor",
                "cursor_launch_command": r"C:\Apps\Cursor\Cursor.exe",
                "cursor_launch_timeout": 8.0,
                "cursor_launch_poll_interval": 0.2,
                "cursor_composer_click_rel_x": 0.83,
                "cursor_composer_click_rel_y": 0.97,
            }
        }

        driver = router.create_driver_from_config(config)

        self.assertIsInstance(driver, CursorDriver)
        self.assertEqual(driver.window_title, "Fresh Cursor")
        self.assertEqual(driver.launch_command, r"C:\Apps\Cursor\Cursor.exe")
        self.assertEqual(driver.launch_timeout, 8.0)
        self.assertEqual(driver.launch_poll_interval, 0.2)
        self.assertFalse(hasattr(driver, "composer_click_rel_x"))
        self.assertFalse(hasattr(driver, "composer_click_rel_y"))

    def test_create_driver_rejects_unknown_target(self) -> None:
        with self.assertRaises(ValueError) as context:
            create_driver("unknown")

        self.assertIn("Unknown executor target", str(context.exception))


if __name__ == "__main__":
    unittest.main()
