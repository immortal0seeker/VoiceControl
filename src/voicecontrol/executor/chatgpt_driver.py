"""ChatGPT Desktop driver."""

from __future__ import annotations

import logging

from voicecontrol.config import settings
from voicecontrol.executor.app_driver import LaunchableAppDriver
from voicecontrol.executor.window_utils import WindowError

logger = logging.getLogger(__name__)


class ChatGPTDriver(LaunchableAppDriver):
    """Sends prompts to the ChatGPT Desktop window."""

    app_name = "ChatGPT Desktop"

    def __init__(
        self,
        window_title: str = settings.CHATGPT_WINDOW_TITLE,
        launch_command: str = settings.CHATGPT_LAUNCH_COMMAND,
        launch_timeout: float = settings.CHATGPT_LAUNCH_TIMEOUT,
        launch_poll_interval: float = settings.CHATGPT_LAUNCH_POLL_INTERVAL,
    ) -> None:
        super().__init__(
            window_title=window_title,
            launch_command=launch_command,
            launch_timeout=launch_timeout,
            launch_poll_interval=launch_poll_interval,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    import sys

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    driver = ChatGPTDriver()
    try:
        window = driver.find()
        print(f"Found {driver.app_name}: [{window.hwnd}] {window.title!r}")
        driver.send_prompt("你好，这是一条来自 VoiceControl 的 ChatGPT 测试消息。")
        print("Sent test prompt.")
    except WindowError as exc:
        print(f"ERROR: {exc}")
