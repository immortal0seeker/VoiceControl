"""Read and write the user-facing JSON configuration.

This module provides the UI/settings layer with a safe way to load, merge,
and save ``config.json``. It intentionally does not import ``settings.py`` so
``settings.py`` can import this module without a circular import.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
CONFIG_PATH: Path = PROJECT_ROOT / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "audio": {
        "input_device": None,
    },
    "stt": {
        "whisper_model_size": "small",
        "whisper_device": "cuda",
        "whisper_compute_type": "float16",
        "whisper_language": None,
        "whisper_beam_size": 5,
        "whisper_vad_filter": True,
        "whisper_condition_on_previous_text": False,
    },
    "vad": {
        "speech_threshold": 0.5,
        "silence_duration": 3.0,
        "min_speech_duration": 0.3,
        "max_record_seconds": 180.0,
        "start_timeout": 8.0,
        "poll_interval": 0.15,
    },
    "executor": {
        "codex_window_title": "Codex",
        "codex_launch_command": "",
        "codex_launch_timeout": 15.0,
        "codex_launch_poll_interval": 0.5,
        "send_prompt_auto_enter": True,
        "click_composer_before_paste": True,
        "composer_click_rel_x": 0.5,
        "composer_click_rel_y": 0.9,
    },
    "wake_word": {
        "model": "hey_jarvis",
        "threshold": 0.5,
        "cooldown": 2.0,
    },
    "feedback": {
        "enabled": True,
        "wake_freq": 880,
        "wake_ms": 150,
        "done_freq": 1320,
        "done_ms": 120,
    },
    "tts": {
        "enabled": True,
        "rate": 0,
        "volume": 100,
        "voice": None,
    },
    "hotkeys": {
        "record_hotkey": "f9",
        "quit_hotkey": "esc",
    },
    "desktop_pet": {
        "animation_enabled": True,
    },
}


class ConfigError(RuntimeError):
    """Raised when ``config.json`` cannot be read or written."""


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Return ``defaults`` recursively updated with ``overrides``."""
    merged = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    """Load ``config.json`` and merge it over ``DEFAULT_CONFIG``."""
    config_path = Path(path)
    if not config_path.exists():
        return deepcopy(DEFAULT_CONFIG)

    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {config_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Failed to read {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"Expected top-level JSON object in {config_path}.")
    return _deep_merge(DEFAULT_CONFIG, raw)


def save_config(config: dict[str, Any], path: str | Path = CONFIG_PATH) -> Path:
    """Save ``config`` to ``config.json`` using stable pretty formatting."""
    config_path = Path(path)
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except OSError as exc:
        raise ConfigError(f"Failed to write {config_path}: {exc}") from exc
    return config_path


def ensure_config(path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    """Create ``config.json`` with defaults if missing, then return config."""
    config_path = Path(path)
    config = load_config(config_path)
    if not config_path.exists():
        save_config(config, config_path)
    return config
