"""Codex Desktop driver — the first concrete AppDriver."""

from __future__ import annotations

import logging

from voicecontrol.config import settings
from voicecontrol.executor.app_driver import AppDriver
from voicecontrol.executor.window_utils import WindowError

logger = logging.getLogger(__name__)


class CodexDriver(AppDriver):
    """Sends prompts to the Codex Desktop window."""

    app_name = "Codex Desktop"

    def __init__(self, window_title: str = settings.CODEX_WINDOW_TITLE) -> None:
        self.window_title = window_title


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
