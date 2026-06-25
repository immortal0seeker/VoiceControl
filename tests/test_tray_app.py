from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from PIL import Image

from voicecontrol import tray_app


class TraySettingsLauncherTests(unittest.TestCase):
    def test_open_settings_launches_settings_module_with_current_python(self) -> None:
        with patch.object(tray_app.subprocess, "Popen") as popen:
            tray_app.open_settings_window()

        popen.assert_called_once_with(
            [sys.executable, "-m", "voicecontrol.ui.settings_app"],
            close_fds=True,
        )


class TrayIconTests(unittest.TestCase):
    def test_load_tray_icon_image_prefers_ui_asset_png(self) -> None:
        image = tray_app._load_tray_icon_image()

        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.mode, "RGBA")
        self.assertEqual(image.size, (128, 128))

    def test_load_tray_icon_image_falls_back_when_asset_is_missing(self) -> None:
        with (
            patch("voicecontrol.ui.assets.asset_path", side_effect=OSError("missing")),
            patch.object(tray_app.logger, "exception") as log_exception,
        ):
            image = tray_app._load_tray_icon_image()

        log_exception.assert_called_once()
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.mode, "RGBA")
        self.assertEqual(image.size, (64, 64))


if __name__ == "__main__":
    unittest.main()
