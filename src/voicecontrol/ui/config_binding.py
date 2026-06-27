"""Config binding helpers for the settings UI.

Provides lightweight utilities for reading nested config dicts and collecting
widget→config-path mappings used by SettingsPage to save user input.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# A Binding pairs a config key path with a callable that reads the current
# widget value.  Collected by SettingsPage, consumed when the user saves.
Binding = tuple[tuple[str, ...], Callable[[], Any]]


def get_nested(config: dict[str, Any], path: tuple[str, ...]) -> Any:
    """Return the value at *path* inside the nested *config* dict."""
    value: Any = config
    for key in path:
        value = value[key]
    return value


def set_nested(config: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    """Set the value at *path* inside the nested *config* dict in-place."""
    target = config
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def optional_float_text(text: str) -> float | None:
    """Parse *text* as float, returning ``None`` for blank input."""
    stripped = text.strip()
    return None if stripped == "" else float(stripped)


def register(
    bindings: list[Binding],
    path: tuple[str, ...],
    reader: Callable[[], Any],
) -> None:
    """Append a *(path, reader)* pair to *bindings*."""
    bindings.append((path, reader))
