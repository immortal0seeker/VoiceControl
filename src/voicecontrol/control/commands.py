"""File-based control commands consumed by the tray daemon."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Literal

from voicecontrol.config import settings

START_RECORDING = "start_recording"
STOP_RECORDING = "stop_recording"
PAUSE_LISTENING = "pause_listening"
RESUME_LISTENING = "resume_listening"
RELOAD_EXECUTOR = "reload_executor"
VALID_COMMANDS = {START_RECORDING, STOP_RECORDING, PAUSE_LISTENING, RESUME_LISTENING, RELOAD_EXECUTOR}
ControlCommand = Literal["start_recording", "stop_recording", "pause_listening", "resume_listening", "reload_executor"]

CONTROL_COMMAND_PATH = settings.RUNTIME_DIR / "control_command.json"
CONTROL_RESPONSE_PATH = settings.RUNTIME_DIR / "control_response.json"


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


def write_control_response(
    command: ControlCommand,
    status: Literal["ok", "error"],
    message: str,
    path: str | Path = CONTROL_RESPONSE_PATH,
) -> Path:
    """Write the outcome of a consumed control command."""
    if command not in VALID_COMMANDS:
        raise ValueError(f"Unsupported control command: {command}")
    response_path = Path(path)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "command": command,
        "status": status,
        "message": message,
        "created_at": time.time(),
    }
    response_path.write_text(json.dumps(payload), encoding="utf-8")
    return response_path


def read_control_response(
    path: str | Path = CONTROL_RESPONSE_PATH,
    max_age_seconds: float = 10.0,
) -> dict[str, Any] | None:
    """Read the latest control response if it is recent and well-formed."""
    response_path = Path(path)
    if not response_path.exists():
        return None

    try:
        raw = json.loads(response_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(raw, dict):
        return None
    command = raw.get("command")
    status = raw.get("status")
    created_at = raw.get("created_at")
    if command not in VALID_COMMANDS:
        return None
    if status not in {"ok", "error"}:
        return None
    if not isinstance(created_at, int | float):
        return None
    if time.time() - float(created_at) > max_age_seconds:
        return None
    return raw
