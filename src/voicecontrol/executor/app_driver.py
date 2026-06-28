"""Pluggable driver interface for target applications.

One driver per target app (Codex, ChatGPT, Cursor, ...). Drivers focus the
app window and send a prompt via clipboard paste + Enter (preferred over
char-by-char typing for Chinese / long prompts).
"""

from __future__ import annotations

import logging
import subprocess
import time
from abc import ABC

import keyboard
import pyperclip

from voicecontrol.config import settings
from voicecontrol.executor.window_utils import (
    Window,
    WindowError,
    click_in_window,
    find_window,
    focus_window,
)

logger = logging.getLogger(__name__)


class AppDriver(ABC):
    """Base driver: locate + focus a window, then paste & submit a prompt.

    Subclasses set ``app_name`` and ``window_title`` (a case-insensitive
    substring of the target window's title).
    """

    app_name: str = "App"
    window_title: str = ""

    def find(self) -> Window:
        """Locate the target window, raising ``WindowError`` if absent."""
        window = find_window(self.window_title)
        if window is None:
            raise WindowError(
                f"{self.app_name} window not found "
                f"(looking for title containing '{self.window_title}'). "
                f"Is the app running?"
            )
        return window

    def focus(self) -> Window:
        """Bring the target app window to the foreground; return the window."""
        window = self.find()
        focus_window(window, settle_delay=settings.FOCUS_SETTLE_DELAY)
        return window

    def _focus_composer(self, window: Window) -> None:
        """Click the input box so pasted text lands in it (override per app)."""
        if settings.CLICK_COMPOSER_BEFORE_PASTE:
            click_in_window(
                window,
                settings.COMPOSER_CLICK_REL_X,
                settings.COMPOSER_CLICK_REL_Y,
                settle_delay=settings.CLICK_SETTLE_DELAY,
            )

    def send_prompt(self, text: str, auto_enter: bool | None = None) -> None:
        """Focus the app, paste ``text`` from the clipboard, then press Enter.

        ``auto_enter`` defaults to ``settings.SEND_PROMPT_AUTO_ENTER``.
        """
        if not text.strip():
            logger.warning("Empty prompt; nothing sent to %s.", self.app_name)
            return

        if auto_enter is None:
            auto_enter = settings.SEND_PROMPT_AUTO_ENTER

        window = self.focus()
        self._focus_composer(window)

        try:
            pyperclip.copy(text)
        except Exception as exc:
            raise WindowError(f"Failed to set clipboard: {exc}") from exc

        logger.info("Pasting %d chars into %s", len(text), self.app_name)
        time.sleep(settings.PASTE_DELAY)
        keyboard.send("ctrl+v")

        if auto_enter:
            time.sleep(settings.ENTER_DELAY)
            keyboard.send("enter")
            logger.info("Submitted prompt to %s.", self.app_name)


class LaunchableAppDriver(AppDriver):
    """App driver that can start the target app when its window is absent."""

    launch_command: str = ""
    launch_timeout: float = settings.CODEX_LAUNCH_TIMEOUT
    launch_poll_interval: float = settings.CODEX_LAUNCH_POLL_INTERVAL

    def __init__(
        self,
        window_title: str,
        launch_command: str = "",
        launch_timeout: float = settings.CODEX_LAUNCH_TIMEOUT,
        launch_poll_interval: float = settings.CODEX_LAUNCH_POLL_INTERVAL,
    ) -> None:
        self.window_title = window_title
        self.launch_command = launch_command
        self.launch_timeout = launch_timeout
        self.launch_poll_interval = launch_poll_interval

    def find(self) -> Window:
        """Locate the target window, optionally launching the app first."""
        window = find_window(self.window_title)
        if window is not None:
            return window

        if not self.launch_command.strip():
            raise WindowError(
                f"{self.app_name} window not found "
                f"(looking for title containing '{self.window_title}'). "
                f"Is the app running?"
            )

        logger.info(
            "%s window not found; launching with configured command.",
            self.app_name,
        )
        try:
            subprocess.Popen(self.launch_command)
        except Exception as exc:
            logger.error("Failed to launch %s: %s", self.app_name, exc)
            raise WindowError(f"Failed to launch {self.app_name}: {exc}") from exc

        deadline = time.monotonic() + self.launch_timeout
        while time.monotonic() < deadline:
            time.sleep(self.launch_poll_interval)
            window = find_window(self.window_title)
            if window is not None:
                logger.info("%s window appeared after launch.", self.app_name)
                return window

        logger.error(
            "%s launch timed out after %.1fs waiting for title containing '%s'.",
            self.app_name,
            self.launch_timeout,
            self.window_title,
        )
        raise WindowError(
            f"{self.app_name} launched but no matching window appeared within "
            f"{self.launch_timeout:.1f}s."
        )
