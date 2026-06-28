"""Factory for selecting the configured target application driver."""

from __future__ import annotations

from collections.abc import Callable

from voicecontrol.config import settings
from voicecontrol.executor.app_driver import AppDriver
from voicecontrol.executor.chatgpt_driver import ChatGPTDriver
from voicecontrol.executor.codex_driver import CodexDriver
from voicecontrol.executor.cursor_driver import CursorDriver


DriverFactory = Callable[[], AppDriver]

DRIVER_FACTORIES: dict[str, DriverFactory] = {
    "codex": CodexDriver,
    "chatgpt": ChatGPTDriver,
    "cursor": CursorDriver,
}


def normalize_target(target: str) -> str:
    """Return the canonical executor target key."""
    return target.strip().lower()


def create_driver(target: str | None = None) -> AppDriver:
    """Create an app driver for *target*, defaulting to settings."""
    key = normalize_target(target or settings.DEFAULT_EXECUTOR_TARGET)
    try:
        factory = DRIVER_FACTORIES[key]
    except KeyError as exc:
        choices = ", ".join(sorted(DRIVER_FACTORIES))
        raise ValueError(f"Unknown executor target '{target}'. Expected one of: {choices}.") from exc
    return factory()


def get_default_driver() -> AppDriver:
    """Create the app driver configured as the default executor target."""
    return create_driver(settings.DEFAULT_EXECUTOR_TARGET)
