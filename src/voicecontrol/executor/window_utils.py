"""Windows window discovery and focusing helpers.

Shared by the executor drivers. Uses the Win32 API via pywin32 for reliable
window enumeration and foreground activation. No STT or recording logic here.

Run as a script to list all visible top-level windows — useful for finding a
target application's exact title (e.g. ChatGPT Classic).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import win32api
import win32con
import win32gui

logger = logging.getLogger(__name__)


class WindowError(RuntimeError):
    """Raised when a target window cannot be found or focused."""


@dataclass(frozen=True)
class Window:
    """A visible top-level window."""

    hwnd: int
    title: str


def list_windows() -> list[Window]:
    """Return all visible top-level windows that have a non-empty title."""
    windows: list[Window] = []

    def _callback(hwnd: int, _: object) -> bool:
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.strip():
                windows.append(Window(hwnd=hwnd, title=title))
        return True

    win32gui.EnumWindows(_callback, None)
    return windows


def find_window(title_substring: str) -> Window | None:
    """Prefer an exact visible title, then fall back to a substring match.

    Matching is case-insensitive.
    """
    needle = title_substring.casefold()
    windows = list_windows()
    for window in windows:
        if window.title.casefold() == needle:
            return window
    for window in windows:
        if needle in window.title.casefold():
            return window
    return None


def focus_window(window: Window, settle_delay: float = 0.3) -> None:
    """Bring ``window`` to the foreground.

    Restores the window if minimized, then activates it. Raises ``WindowError``
    if activation fails (e.g. focus stolen, permission boundary).
    """
    try:
        placement = win32gui.GetWindowPlacement(window.hwnd)
        if placement[1] == win32con.SW_SHOWMINIMIZED:
            win32gui.ShowWindow(window.hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(window.hwnd)
    except Exception as exc:
        raise WindowError(
            f"Failed to focus window '{window.title}': {exc}"
        ) from exc

    time.sleep(settle_delay)
    foreground = win32gui.GetForegroundWindow()
    if foreground != window.hwnd:
        logger.warning(
            "Focus may not have taken: requested '%s' but foreground hwnd differs.",
            window.title,
        )


def click_in_window(
    window: Window,
    rel_x: float,
    rel_y: float,
    settle_delay: float = 0.15,
) -> None:
    """Left-click inside ``window`` at a point relative to its rectangle.

    ``rel_x``/``rel_y`` are fractions (0.0-1.0) of the window width/height.
    Used to put the caret in an app's input box before pasting.
    """
    try:
        left, top, right, bottom = win32gui.GetWindowRect(window.hwnd)
    except Exception as exc:
        raise WindowError(f"Failed to read window rect: {exc}") from exc

    x = left + int((right - left) * rel_x)
    y = top + int((bottom - top) * rel_y)
    logger.info("Clicking input at (%d, %d) in '%s'", x, y, window.title)

    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(settle_delay)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    import sys

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    found = list_windows()
    print(f"Found {len(found)} visible window(s):\n")
    for win in found:
        print(f"  [{win.hwnd}] {win.title}")
