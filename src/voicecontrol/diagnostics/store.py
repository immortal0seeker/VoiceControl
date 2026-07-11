"""Append-only diagnostic result storage."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from voicecontrol.config import settings


@dataclass(frozen=True)
class DiagnosticResult:
    """One diagnostic test result."""

    name: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at.isoformat(timespec="seconds"),
            "name": self.name,
            "status": self.status,
            "details": self.details,
            "error": self.error,
        }


def append_diagnostic_result(
    result: DiagnosticResult,
    path: str | Path | None = None,
) -> Path:
    """Append ``result`` as one JSON line and return the diagnostics path."""
    diagnostic_path = Path(path) if path is not None else settings.DIAGNOSTICS_HISTORY_PATH
    diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(result.to_json_dict(), ensure_ascii=False) + "\n"
    with diagnostic_path.open("a", encoding="utf-8") as file:
        file.write(line)
    return diagnostic_path
