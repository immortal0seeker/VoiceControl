from __future__ import annotations

import unittest

from voicecontrol.executor.chatgpt_driver import ChatGPTDriver
from voicecontrol.executor.codex_driver import CodexDriver
from voicecontrol.executor.cursor_driver import CursorDriver
from voicecontrol.executor.router import create_driver


class ExecutorRouterTests(unittest.TestCase):
    def test_create_driver_returns_requested_target_driver(self) -> None:
        self.assertIsInstance(create_driver("codex"), CodexDriver)
        self.assertIsInstance(create_driver("chatgpt"), ChatGPTDriver)
        self.assertIsInstance(create_driver("cursor"), CursorDriver)

    def test_create_driver_rejects_unknown_target(self) -> None:
        with self.assertRaises(ValueError) as context:
            create_driver("unknown")

        self.assertIn("Unknown executor target", str(context.exception))


if __name__ == "__main__":
    unittest.main()
