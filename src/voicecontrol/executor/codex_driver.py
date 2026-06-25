"""Codex Desktop driver — the first concrete AppDriver."""

from __future__ import annotations

import logging
import subprocess
import time

from voicecontrol.config import settings
from voicecontrol.executor.app_driver import AppDriver
from voicecontrol.executor.window_utils import Window, WindowError, find_window, focus_window

logger = logging.getLogger(__name__)


class CodexDriver(AppDriver):
    """Sends prompts to the Codex Desktop window."""

    app_name = "Codex Desktop"

    def __init__(
        self,
        window_title: str = settings.CODEX_WINDOW_TITLE,
        launch_command: str = settings.CODEX_LAUNCH_COMMAND,
        launch_timeout: float = settings.CODEX_LAUNCH_TIMEOUT,
        launch_poll_interval: float = settings.CODEX_LAUNCH_POLL_INTERVAL,
    ) -> None:
        self.window_title = window_title
        self.launch_command = launch_command
        self.launch_timeout = launch_timeout
        self.launch_poll_interval = launch_poll_interval

    def find(self) -> Window:
        """Locate Codex, optionally launching it when no window is present."""
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

    def focus(self) -> Window:
        """Bring Codex to foreground, launching it first if configured."""
        window = self.find()
        focus_window(window, settle_delay=settings.FOCUS_SETTLE_DELAY)
        return window


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    import sys

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    driver = CodexDriver()
    try:
        window = driver.find()
        print(f"Found {driver.app_name}: [{window.hwnd}] {window.title!r}")
        driver.send_prompt("你好，这是一条来自 VoiceControl 的测试消息。")
        print("Sent test prompt.")
    except WindowError as exc:
        print(f"ERROR: {exc}")
