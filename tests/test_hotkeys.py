from __future__ import annotations

import unittest
from unittest.mock import patch

from voicecontrol.utils.hotkeys import ManualStopHotkey


class ManualStopHotkeyTests(unittest.TestCase):
    def test_press_sets_stop_event_after_debounce_and_unhooks_on_exit(self) -> None:
        callbacks: list[object] = []

        def on_press_key(_key: str, callback, suppress: bool = False) -> str:  # noqa: ANN001
            del suppress
            callbacks.append(callback)
            return "handler"

        with (
            patch("voicecontrol.utils.hotkeys.keyboard.on_press_key", side_effect=on_press_key),
            patch("voicecontrol.utils.hotkeys.keyboard.unhook") as unhook,
            patch("voicecontrol.utils.hotkeys.time.monotonic", side_effect=[10.0, 10.1, 10.5]),
        ):
            with ManualStopHotkey("f9") as stop_event:
                self.assertFalse(stop_event.is_set())
                callbacks[0](object())
                self.assertFalse(stop_event.is_set())
                callbacks[0](object())
                self.assertTrue(stop_event.is_set())

        unhook.assert_called_once_with("handler")


if __name__ == "__main__":
    unittest.main()
