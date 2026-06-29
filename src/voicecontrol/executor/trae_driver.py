"""Trae driver."""

from __future__ import annotations

import logging
import time

import keyboard

from voicecontrol.config import settings
from voicecontrol.executor.app_driver import LaunchableAppDriver
from voicecontrol.executor.window_utils import Window, WindowError, click_in_window

logger = logging.getLogger(__name__)


class TraeDriver(LaunchableAppDriver):
    """Sends prompts to the Trae window."""

    app_name = "Trae"
    AI_SIDEBAR_SHORTCUT = "ctrl+u"

    def __init__(
        self,
        window_title: str = settings.TRAE_WINDOW_TITLE,
        launch_command: str = settings.TRAE_LAUNCH_COMMAND,
        launch_timeout: float = settings.TRAE_LAUNCH_TIMEOUT,
        launch_poll_interval: float = settings.TRAE_LAUNCH_POLL_INTERVAL,
        neutral_click_rel_x: float = settings.TRAE_NEUTRAL_CLICK_REL_X,
        neutral_click_rel_y: float = settings.TRAE_NEUTRAL_CLICK_REL_Y,
        ai_sidebar_shortcut: str = settings.TRAE_AI_SIDEBAR_SHORTCUT,
    ) -> None:
        super().__init__(
            window_title=window_title,
            launch_command=launch_command,
            launch_timeout=launch_timeout,
            launch_poll_interval=launch_poll_interval,
        )
        self.neutral_click_rel_x = neutral_click_rel_x
        self.neutral_click_rel_y = neutral_click_rel_y
        self.ai_sidebar_shortcut = ai_sidebar_shortcut

    def _focus_composer(self, window: Window) -> None:
        """Defocus Trae's AI sidebar, then use its shortcut to focus input."""
        if settings.CLICK_COMPOSER_BEFORE_PASTE:
            click_in_window(
                window,
                self.neutral_click_rel_x,
                self.neutral_click_rel_y,
                settle_delay=settings.CLICK_SETTLE_DELAY,
            )
            keyboard.send(self.ai_sidebar_shortcut)
            time.sleep(settings.CLICK_SETTLE_DELAY)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    import sys

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    driver = TraeDriver()
    try:
        window = driver.find()
        print(f"Found {driver.app_name}: [{window.hwnd}] {window.title!r}")
        driver.send_prompt("你好，这是一条来自 VoiceControl 的 Trae 测试消息。")
        print("Sent test prompt.")
    except WindowError as exc:
        print(f"ERROR: {exc}")
