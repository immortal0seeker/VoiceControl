"""Factory for selecting the configured target application driver."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from voicecontrol.config import settings
from voicecontrol.executor.app_driver import AppDriver
from voicecontrol.executor.chatgpt_driver import ChatGPTDriver
from voicecontrol.executor.codex_driver import CodexDriver
from voicecontrol.executor.cursor_driver import CursorDriver
from voicecontrol.executor.trae_driver import TraeDriver


DriverFactory = Callable[[], AppDriver]

DRIVER_FACTORIES: dict[str, DriverFactory] = {
    "codex": CodexDriver,
    "chatgpt": ChatGPTDriver,
    "cursor": CursorDriver,
    "trae": TraeDriver,
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


def _executor_config(config: dict[str, Any]) -> dict[str, Any]:
    executor = config.get("executor", {})
    if not isinstance(executor, dict):
        raise ValueError("Expected executor config to be an object.")
    return executor


def create_driver_from_config(config: dict[str, Any], target: str | None = None) -> AppDriver:
    """Create a driver from a freshly loaded config dict."""
    executor = _executor_config(config)
    key = normalize_target(target or executor.get("default_target", settings.DEFAULT_EXECUTOR_TARGET))
    if key == "codex":
        return CodexDriver(
            window_title=executor.get("codex_window_title", settings.CODEX_WINDOW_TITLE),
            launch_command=executor.get("codex_launch_command", settings.CODEX_LAUNCH_COMMAND),
            launch_timeout=executor.get("codex_launch_timeout", settings.CODEX_LAUNCH_TIMEOUT),
            launch_poll_interval=executor.get(
                "codex_launch_poll_interval",
                settings.CODEX_LAUNCH_POLL_INTERVAL,
            ),
        )
    if key == "chatgpt":
        return ChatGPTDriver(
            window_title=executor.get("chatgpt_window_title", settings.CHATGPT_WINDOW_TITLE),
            launch_command=executor.get("chatgpt_launch_command", settings.CHATGPT_LAUNCH_COMMAND),
            launch_timeout=executor.get("chatgpt_launch_timeout", settings.CHATGPT_LAUNCH_TIMEOUT),
            launch_poll_interval=executor.get(
                "chatgpt_launch_poll_interval",
                settings.CHATGPT_LAUNCH_POLL_INTERVAL,
            ),
        )
    if key == "cursor":
        return CursorDriver(
            window_title=executor.get("cursor_window_title", settings.CURSOR_WINDOW_TITLE),
            launch_command=executor.get("cursor_launch_command", settings.CURSOR_LAUNCH_COMMAND),
            launch_timeout=executor.get("cursor_launch_timeout", settings.CURSOR_LAUNCH_TIMEOUT),
            launch_poll_interval=executor.get(
                "cursor_launch_poll_interval",
                settings.CURSOR_LAUNCH_POLL_INTERVAL,
            ),
        )
    if key == "trae":
        return TraeDriver(
            window_title=executor.get("trae_window_title", settings.TRAE_WINDOW_TITLE),
            launch_command=executor.get("trae_launch_command", settings.TRAE_LAUNCH_COMMAND),
            launch_timeout=executor.get("trae_launch_timeout", settings.TRAE_LAUNCH_TIMEOUT),
            launch_poll_interval=executor.get(
                "trae_launch_poll_interval",
                settings.TRAE_LAUNCH_POLL_INTERVAL,
            ),
            neutral_click_rel_x=executor.get(
                "trae_neutral_click_rel_x",
                settings.TRAE_NEUTRAL_CLICK_REL_X,
            ),
            neutral_click_rel_y=executor.get(
                "trae_neutral_click_rel_y",
                settings.TRAE_NEUTRAL_CLICK_REL_Y,
            ),
            ai_sidebar_shortcut=executor.get(
                "trae_ai_sidebar_shortcut",
                settings.TRAE_AI_SIDEBAR_SHORTCUT,
            ),
        )
    choices = ", ".join(sorted(DRIVER_FACTORIES))
    raise ValueError(f"Unknown executor target '{target}'. Expected one of: {choices}.")


def get_default_driver() -> AppDriver:
    """Create the app driver configured as the default executor target."""
    return create_driver(settings.DEFAULT_EXECUTOR_TARGET)
