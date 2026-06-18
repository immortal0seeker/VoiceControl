"""Audible feedback cues.

Short beeps so the user knows the wake word was heard and the command was
sent — important when running headless in the tray with no console. Uses the
stdlib ``winsound`` (Windows only); failures are swallowed so audio issues
never break the pipeline.
"""

from __future__ import annotations

import logging

from voicecontrol.config import settings

logger = logging.getLogger(__name__)

try:
    import winsound
except ImportError:  # non-Windows; feedback becomes a no-op
    winsound = None


def _beep(frequency: int, duration_ms: int) -> None:
    if not settings.FEEDBACK_ENABLED or winsound is None:
        return
    try:
        winsound.Beep(frequency, duration_ms)
    except Exception as exc:  # pragma: no cover - audio device quirks
        logger.debug("Beep failed: %s", exc)


def wake_cue() -> None:
    """Play the 'wake word heard, listening now' cue."""
    _beep(settings.FEEDBACK_WAKE_FREQ, settings.FEEDBACK_WAKE_MS)


def done_cue() -> None:
    """Play the 'command sent' cue."""
    _beep(settings.FEEDBACK_DONE_FREQ, settings.FEEDBACK_DONE_MS)


if __name__ == "__main__":
    print("Playing wake cue, then done cue...")
    wake_cue()
    done_cue()
    print("Done.")
