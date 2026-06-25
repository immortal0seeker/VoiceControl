"""File-based control commands consumed by the tray daemon."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Literal

from voicecontrol.config import settings

START_RECORDING = "start_recording"
STOP_RECORDING = "stop_recording"
VALID_COMMANDS = {START_RECORDING, STOP_RECORDING}
ControlCommand = Literal["start_recording", "stop_recording"]

CONTROL_COMMAND_PATH = settings.LOG_DIR / "control_command.json"


def write_control_command(
    command: ControlCommand,
    path: str | Path = CONTROL_COMMAND_PATH,
) -> Path:
    """Write a command for the tray daemon to consume."""
    if command not in VALID_COMMANDS:
        raise ValueError(f"Unsupported control command: {command}")
    command_path = Path(path)
    command_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"command": command, "created_at": time.time()}
    command_path.write_text(json.dumps(payload), encoding="utf-8")
    return command_path


def read_control_command(
    path: str | Path = CONTROL_COMMAND_PATH,
    max_age_seconds: float = 10.0,
) -> ControlCommand | None:
    """Read and consume one pending control command."""
    command_path = Path(path)
    if not command_path.exists():
        return None

    try:
        raw = json.loads(command_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raw = {}
    finally:
        try:
            command_path.unlink()
        except FileNotFoundError:
            pass

    command = raw.get("command") if isinstance(raw, dict) else None
    created_at = raw.get("created_at") if isinstance(raw, dict) else None
    if not isinstance(created_at, int | float):
        return None
    if time.time() - float(created_at) > max_age_seconds:
        return None
    if command in VALID_COMMANDS:
        return command
    return None
