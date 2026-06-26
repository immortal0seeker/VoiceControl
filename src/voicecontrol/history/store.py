"""Append-only command history storage."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

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
