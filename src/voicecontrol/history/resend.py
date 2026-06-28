"""Resend the latest transcribed command from command history."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from voicecontrol.executor.app_driver import AppDriver
from voicecontrol.executor.router import get_default_driver
from voicecontrol.executor.window_utils import WindowError
from voicecontrol.history.store import CommandHistoryRecord, append_command_history, latest_command_with_text

logger = logging.getLogger(__name__)


class ResendError(RuntimeError):
    """Raised when there is no command available to resend."""


@dataclass(frozen=True)
class ResendResult:
    """Outcome of resending a command."""

    text: str
    sent: bool
    send_error: str | None = None


def resend_last_command(
    driver: AppDriver | None = None,
    history_path: str | Path | None = None,
) -> ResendResult:
    """Send the latest non-empty command text and append the resend outcome."""
    record = latest_command_with_text(path=history_path)
    if record is None:
        raise ResendError("No command with recognized text found in history.")

    target_driver = driver or get_default_driver()
    sent = False
    send_error: str | None = None
    try:
        target_driver.send_prompt(record.text)
        sent = True
    except WindowError as exc:
        send_error = str(exc)
        logger.warning("Could not resend command: %s", exc)

    append_command_history(
        CommandHistoryRecord(
            text=record.text,
            wav_path=record.wav_path,
            sent=sent,
            send_error=send_error,
        ),
        path=history_path,
    )
    return ResendResult(text=record.text, sent=sent, send_error=send_error)
