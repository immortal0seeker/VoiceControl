from __future__ import annotations

import threading
import unittest
from unittest.mock import Mock

from voicecontrol import tray_app


class TrayRecordingControlTests(unittest.TestCase):
    def _app(self) -> tray_app.TrayApp:
        app = tray_app.TrayApp.__new__(tray_app.TrayApp)
        app._manual_record_event = threading.Event()
        app._recording_stop_event = threading.Event()
        app._is_recording = False
        app._icon = Mock()
        return app

    def test_recording_menu_label_changes_with_recording_state(self) -> None:
        app = self._app()

        self.assertEqual(app._recording_label(Mock()), "开始录音")

        app._is_recording = True

        self.assertEqual(app._recording_label(Mock()), "停止录音")

    def test_recording_menu_starts_recording_when_idle(self) -> None:
        app = self._app()

        app._on_toggle_recording(Mock(), Mock())

        self.assertTrue(app._manual_record_event.is_set())
        self.assertFalse(app._recording_stop_event.is_set())
        self.assertTrue(app._is_recording)
        app._icon.update_menu.assert_called_once()

    def test_recording_menu_stops_recording_when_active(self) -> None:
        app = self._app()
        app._is_recording = True

        app._on_toggle_recording(Mock(), Mock())

        self.assertTrue(app._recording_stop_event.is_set())
        self.assertFalse(app._manual_record_event.is_set())
        self.assertFalse(app._is_recording)
        app._icon.update_menu.assert_called_once()

    def test_recording_state_follows_pipeline_stage(self) -> None:
        app = self._app()

        app._set_stage("wake")
        self.assertTrue(app._is_recording)

        app._set_stage("transcribing")
        self.assertFalse(app._is_recording)

    def test_control_command_start_and_stop_update_recording_state(self) -> None:
        app = self._app()

        app._handle_control_command("start_recording")
        self.assertTrue(app._manual_record_event.is_set())
        self.assertTrue(app._is_recording)

        app._handle_control_command("stop_recording")
        self.assertTrue(app._recording_stop_event.is_set())
        self.assertFalse(app._is_recording)


if __name__ == "__main__":
    unittest.main()
