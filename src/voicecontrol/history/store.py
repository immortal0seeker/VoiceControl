"""Append-only command history storage."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from voicecontrol.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandHistoryRecord:
    """One processed voice command and its outcome."""

    text: str
    wav_path: Path
    sent: bool
    send_error: str | None = None
    error: str | None = None
    raw_text: str | None = None
    stt_engine: str | None = None
    stt_model: str | None = None
    stt_language: str | None = None
    stt_language_probability: float | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "created_at": self.created_at.isoformat(timespec="seconds"),
            "text": self.text,
            "wav_path": self.wav_path.as_posix(),
            "sent": self.sent,
            "send_error": self.send_error,
            "error": self.error,
            "raw_text": self.raw_text,
            "stt_engine": self.stt_engine,
            "stt_model": self.stt_model,
            "stt_language": self.stt_language,
            "stt_language_probability": self.stt_language_probability,
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
            raw_text=data.get("raw_text") if isinstance(data.get("raw_text"), str) else None,
            stt_engine=data.get("stt_engine") if isinstance(data.get("stt_engine"), str) else None,
            stt_model=data.get("stt_model") if isinstance(data.get("stt_model"), str) else None,
            stt_language=data.get("stt_language") if isinstance(data.get("stt_language"), str) else None,
            stt_language_probability=(
                float(data["stt_language_probability"])
                if isinstance(data.get("stt_language_probability"), int | float)
                else None
            ),
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
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
                if not isinstance(data, dict):
                    raise TypeError("history record is not a JSON object")
                records.append(CommandHistoryRecord.from_json_dict(data))
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning(
                    "Skipping invalid command history line %d in %s: %s",
                    line_number,
                    history_path,
                    exc,
                )
    return records


def latest_command_with_text(path: str | Path | None = None) -> CommandHistoryRecord | None:
    """Return the latest history record containing non-empty text."""
    for record in reversed(read_command_history(path=path)):
        if record.text.strip():
            return record
    return None
