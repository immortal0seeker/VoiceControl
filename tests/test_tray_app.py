from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from voicecontrol import tray_app


class TraySettingsLauncherTests(unittest.TestCase):
    def test_open_settings_launches_settings_module_with_current_python(self) -> None:
        with patch.object(tray_app.subprocess, "Popen") as popen:
            tray_app.open_settings_window()

        popen.assert_called_once_with(
            [sys.executable, "-m", "voicecontrol.ui.settings_app"],
            close_fds=True,
        )


if __name__ == "__main__":
    unittest.main()
