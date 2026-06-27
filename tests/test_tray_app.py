from __future__ import annotations

import sys
import unittest
from unittest.mock import Mock
from unittest.mock import patch

from PIL import Image

from voicecontrol.config import settings
from voicecontrol import tray_app


class TraySettingsLauncherTests(unittest.TestCase):
    def test_open_settings_launches_settings_module_with_current_python(self) -> None:
        with patch.object(tray_app.subprocess, "Popen") as popen:
            tray_app.open_settings_window()

        popen.assert_called_once_with(
            [sys.executable, "-m", "voicecontrol.ui.settings_app"],
            close_fds=True,
        )

    def test_open_settings_menu_item_is_tray_default_action(self) -> None:
        app = tray_app.TrayApp()

        default_items = [item for item in app._icon.menu if item.default]

        self.assertEqual(1, len(default_items))
        self.assertEqual("打开设置", default_items[0].text)


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


class TrayLoggingTests(unittest.TestCase):
    def test_configure_logging_uses_tray_log_directory(self) -> None:
        fake_tray_dir = Mock()
        fake_log_path = settings.TRAY_LOG_DIR / "voicecontrol.log"
        with (
            patch.object(settings, "TRAY_LOG_DIR", fake_tray_dir),
            patch.object(settings, "log_file_path", return_value=fake_log_path),
            patch.object(tray_app.logging, "FileHandler") as file_handler,
            patch.object(tray_app.logging, "basicConfig") as basic_config,
        ):
            tray_app._configure_logging()

        fake_tray_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        file_handler.assert_called_once_with(fake_log_path, encoding="utf-8")
        basic_config.assert_called_once()


if __name__ == "__main__":
    unittest.main()
