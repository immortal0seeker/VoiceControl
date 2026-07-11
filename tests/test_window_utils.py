from __future__ import annotations

from unittest.mock import patch

from voicecontrol.executor.window_utils import Window, find_window


def test_find_window_prefers_exact_title_over_earlier_substring_match() -> None:
    classic = Window(hwnd=1, title="ChatGPT Classic")
    current = Window(hwnd=2, title="ChatGPT")

    with patch(
        "voicecontrol.executor.window_utils.list_windows",
        return_value=[classic, current],
    ):
        found = find_window("ChatGPT")

    assert found == current

