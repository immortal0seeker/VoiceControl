"""Log file inspection helpers."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from voicecontrol.config import settings


def read_recent_log_lines(
    path: str | Path | None = None,
    max_lines: int = 200,
) -> list[str]:
    """Return the last ``max_lines`` from a log file without trailing newlines."""
    log_path = Path(path) if path is not None else settings.log_file_path()
    if max_lines <= 0 or not log_path.exists():
        return []
    with log_path.open("r", encoding="utf-8", errors="replace") as file:
        return [line.rstrip("\r\n") for line in deque(file, maxlen=max_lines)]
