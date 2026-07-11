"""File-backed runtime status snapshot for cross-process UI polling."""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from voicecontrol.config import settings
from voicecontrol.events.status import StatusEvent, StatusType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeStatusSnapshot:
    """A compact status snapshot read by the settings UI."""

    current: str = ""
    message: str = ""
    is_recording: bool = False
    is_sending: bool = False
    last_error: str | None = None
    recent_events: list[dict[str, str]] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "current": self.current,
            "message": self.message,
            "is_recording": self.is_recording,
            "is_sending": self.is_sending,
            "last_error": self.last_error,
            "recent_events": self.recent_events,
            "updated_at": self.updated_at.isoformat(timespec="seconds"),
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, Any]) -> RuntimeStatusSnapshot:
        updated_at_raw = data.get("updated_at")
        updated_at = (
            datetime.fromisoformat(updated_at_raw)
            if isinstance(updated_at_raw, str) and updated_at_raw
            else datetime.now()
        )
        recent_events_raw = data.get("recent_events")
        recent_events = recent_events_raw if isinstance(recent_events_raw, list) else []
        return cls(
            current=str(data.get("current") or ""),
            message=str(data.get("message") or ""),
            is_recording=bool(data.get("is_recording")),
            is_sending=bool(data.get("is_sending")),
            last_error=data.get("last_error") if isinstance(data.get("last_error"), str) else None,
            recent_events=[event for event in recent_events if isinstance(event, dict)],
            updated_at=updated_at,
        )


class RuntimeStatusSnapshotStore:
    """Maintains and writes the latest runtime status snapshot."""

    def __init__(self, path: str | Path | None = None, max_events: int = 8) -> None:
        self._path = Path(path) if path is not None else settings.RUNTIME_STATUS_PATH
        self._max_events = max_events
        self._recent_events: list[dict[str, str]] = []
        self._last_error: str | None = None
        self._lock = threading.Lock()

    def handle_event(self, event: StatusEvent) -> RuntimeStatusSnapshot:
        """Record ``event`` and write the updated snapshot."""
        return self.publish(event.type, message=event.message)

    def publish(self, event_type: StatusType, message: str = "") -> RuntimeStatusSnapshot:
        """Create and persist a snapshot for ``event_type``."""
        with self._lock:
            event_entry = {
                "type": event_type.value,
                "message": message,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
            self._recent_events.append(event_entry)
            self._recent_events = self._recent_events[-self._max_events :]

            if event_type == StatusType.ERROR:
                self._last_error = message or "未知错误"

            snapshot = RuntimeStatusSnapshot(
                current=event_type.value,
                message=message,
                is_recording=event_type == StatusType.RECORDING,
                is_sending=event_type == StatusType.SENDING,
                last_error=self._last_error,
                recent_events=list(self._recent_events),
            )
            write_runtime_status(snapshot, self._path)
            return snapshot


def write_runtime_status(snapshot: RuntimeStatusSnapshot, path: str | Path | None = None) -> Path:
    """Atomically write ``snapshot`` to disk and return the path."""
    status_path = Path(path) if path is not None else settings.RUNTIME_STATUS_PATH
    status_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = status_path.with_name(f".{status_path.name}.{uuid4().hex}.tmp")
    try:
        temp_path.write_text(
            json.dumps(snapshot.to_json_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temp_path, status_path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
    return status_path


def read_runtime_status(path: str | Path | None = None) -> RuntimeStatusSnapshot | None:
    """Read a runtime status snapshot, returning ``None`` if unavailable."""
    status_path = Path(path) if path is not None else settings.RUNTIME_STATUS_PATH
    if not status_path.exists():
        return None
    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.debug("Could not read runtime status snapshot from %s.", status_path)
        return None
    if not isinstance(data, dict):
        return None
    try:
        return RuntimeStatusSnapshot.from_json_dict(data)
    except (TypeError, ValueError):
        logger.debug("Invalid runtime status snapshot in %s.", status_path)
        return None
