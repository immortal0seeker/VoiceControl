from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton, QStackedWidget, QWidget

from voicecontrol.config.manager import load_config
from voicecontrol.ui.settings_window import SettingsWindow


class SettingsWindowNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_window_has_left_navigation_for_recording_and_settings_pages(self) -> None:
        window = SettingsWindow(load_config())

        stack = window.findChild(QStackedWidget, "pageStack")
        recording_page = window.findChild(QWidget, "recordingPage")
        settings_page = window.findChild(QWidget, "settingsPage")
        recording_button = window.findChild(QPushButton, "navRecording")
        settings_button = window.findChild(QPushButton, "navSettings")

        self.assertIsNotNone(stack)
        self.assertIsNotNone(recording_page)
        self.assertIsNotNone(settings_page)
        self.assertIsNotNone(recording_button)
        self.assertIsNotNone(settings_button)
        self.assertEqual(stack.currentWidget(), recording_page)

        settings_button.click()

        self.assertEqual(stack.currentWidget(), settings_page)

    def test_window_allows_null_max_record_seconds_config(self) -> None:
        config = load_config()
        config["vad"]["max_record_seconds"] = None

        try:
            window = SettingsWindow(config)
        except TypeError as exc:
            self.fail(f"null max_record_seconds should be editable in settings: {exc}")

        self.assertIsNotNone(window.findChild(QStackedWidget, "pageStack"))

    def test_settings_page_exposes_codex_launch_command(self) -> None:
        window = SettingsWindow(load_config())

        self.assertIsNotNone(window.findChild(QLineEdit, "codexLaunchCommand"))

    def test_settings_page_exposes_tts_controls(self) -> None:
        window = SettingsWindow(load_config())

        self.assertIsNotNone(window.findChild(QWidget, "ttsEnabled"))
        self.assertIsNotNone(window.findChild(QWidget, "ttsRate"))
        self.assertIsNotNone(window.findChild(QWidget, "ttsVolume"))
        self.assertIsNotNone(window.findChild(QLineEdit, "ttsVoice"))
        self.assertIsNotNone(window.findChild(QPushButton, "testTtsButton"))

    def test_tts_test_button_speaks_sample_phrase(self) -> None:
        window = SettingsWindow(load_config())
        button = window.findChild(QPushButton, "testTtsButton")

        with patch("voicecontrol.ui.settings_window.TextSpeaker") as speaker_class:
            button.click()

        speaker_class.return_value.speak.assert_called_once_with("我在")


if __name__ == "__main__":
    unittest.main()
