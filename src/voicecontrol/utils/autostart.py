"""Launch-at-logon toggle for the tray app.

Uses the per-user registry Run key (HKCU\\...\\Run) so it needs no admin
rights and runs in the interactive user session — required for desktop
automation (a true Windows Service runs in session 0 and cannot focus windows
or send keystrokes). Launches via ``pythonw.exe -m voicecontrol.tray_app``.
"""

from __future__ import annotations

import logging
import sys
import winreg
from pathlib import Path

from voicecontrol.config import settings

logger = logging.getLogger(__name__)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _launch_command() -> str:
    """Build the ``pythonw -m voicecontrol.tray_app`` command used for autostart."""
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    interpreter = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{interpreter}" -m voicecontrol.tray_app'


def is_enabled() -> bool:
    """Return True if the tray app is registered to launch at logon."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, settings.AUTOSTART_APP_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable() -> None:
    """Register the tray app to launch at logon."""
    command = _launch_command()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
        winreg.SetValueEx(key, settings.AUTOSTART_APP_NAME, 0, winreg.REG_SZ, command)
    logger.info("Autostart enabled: %s", command)


def disable() -> None:
    """Remove the tray app from logon autostart (no-op if not set)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, settings.AUTOSTART_APP_NAME)
        logger.info("Autostart disabled.")
    except FileNotFoundError:
        pass


def toggle() -> bool:
    """Flip autostart; return the new state (True = enabled)."""
    if is_enabled():
        disable()
        return False
    enable()
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(f"Autostart enabled: {is_enabled()}")
    print(f"Launch command would be: {_launch_command()}")
