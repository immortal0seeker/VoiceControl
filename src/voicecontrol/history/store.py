"""Append-only command history storage."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from voicecontrol.config import settings


@dataclass(frozen=True)
class CommandHistoryRecord:
    """One processed voice command and its outcome."""

    text: str
    wav_path: Path
    sent: bool
    send_error: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "created_at": self.created_at.isoformat(timespec="seconds"),
            "text": self.text,
            "wav_path": self.wav_path.as_posix(),
            "sent": self.sent,
            "send_error": self.send_error,
            "error": self.error,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, Any]) -> CommandHistoryRecord:
        created_at_raw = data.get("created_at")
        created_at = (
            datetime.fromisoformat(created_at_raw)
            if isinstance(created_at_raw, str) and created_at_raw
            else datetime.now()
        )
        return cls(
            text=str(data.get("text") or ""),
            wav_path=Path(str(data.get("wav_path") or "")),
            sent=bool(data.get("sent")),
            send_error=data.get("send_error") if isinstance(data.get("send_error"), str) else None,
            error=data.get("error") if isinstance(data.get("error"), str) else None,
            created_at=created_at,
        )


def append_command_history(
    record: CommandHistoryRecord,
    path: str | Path | None = None,
) -> Path:
    """Append ``record`` as one JSON line and return the history path."""
    history_path = Path(path) if path is not None else settings.COMMAND_HISTORY_PATH
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as file:
        json.dump(record.to_json_dict(), file, ensure_ascii=False)
        file.write("\n")
    return history_path


def read_command_history(path: str | Path | None = None) -> list[CommandHistoryRecord]:
    """Read command history JSONL records in file order."""
    history_path = Path(path) if path is not None else settings.COMMAND_HISTORY_PATH
    if not history_path.exists():
        return []
    records: list[CommandHistoryRecord] = []
    with history_path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue
            records.append(CommandHistoryRecord.from_json_dict(json.loads(stripped)))
    return records


def latest_command_with_text(path: str | Path | None = None) -> CommandHistoryRecord | None:
    """Return the latest history record containing non-empty text."""
    for record in reversed(read_command_history(path=path)):
        if record.text.strip():
            return record
    return None
