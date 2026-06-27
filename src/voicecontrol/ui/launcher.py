"""Small UI process launch helpers."""

from __future__ import annotations

import subprocess
import sys


def open_control_center() -> None:
    """Open the VoiceControl control center in a separate Python process."""
    subprocess.Popen(
        [sys.executable, "-m", "voicecontrol.ui.settings_app"],
        close_fds=True,
    )
