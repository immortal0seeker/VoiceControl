"""Trae driver."""

from __future__ import annotations

import logging

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
        composer_click_rel_x: float = settings.TRAE_COMPOSER_CLICK_REL_X,
        composer_click_rel_y: float = settings.TRAE_COMPOSER_CLICK_REL_Y,
    ) -> None:
        super().__init__(
            window_title=window_title,
            launch_command=launch_command,
            launch_timeout=launch_timeout,
            launch_poll_interval=launch_poll_interval,
        )
        self.composer_click_rel_x = composer_click_rel_x
        self.composer_click_rel_y = composer_click_rel_y

    def _focus_composer(self, window: Window) -> None:
        """Click the input box in the AI sidebar."""
        if settings.CLICK_COMPOSER_BEFORE_PASTE:
            click_in_window(
                window,
                self.composer_click_rel_x,
                self.composer_click_rel_y,
                settle_delay=settings.CLICK_SETTLE_DELAY,
            )


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
