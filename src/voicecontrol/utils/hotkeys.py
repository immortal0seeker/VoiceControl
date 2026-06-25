"""Small reusable hotkey helpers."""

from __future__ import annotations

import logging
import threading
import time
from types import TracebackType
from typing import Any

import keyboard

logger = logging.getLogger(__name__)


class ManualStopHotkey:
    """Context manager that turns a key press into a recording stop event."""

    def __init__(self, key: str, debounce_seconds: float = 0.4) -> None:
        self.key = key
        self.debounce_seconds = debounce_seconds
        self.stop_event = threading.Event()
        self._handler: Any = None
        self._armed_at = 0.0

    def __enter__(self) -> threading.Event:
        self.stop_event.clear()
        self._armed_at = time.monotonic() + self.debounce_seconds
        self._handler = keyboard.on_press_key(self.key, self._on_press, suppress=False)
        return self.stop_event

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc, traceback
        if self._handler is not None:
            keyboard.unhook(self._handler)
            self._handler = None

    def _on_press(self, _event: object) -> None:
        if time.monotonic() < self._armed_at:
            return
        logger.info("Manual recording stop requested via [%s].", self.key)
        self.stop_event.set()
