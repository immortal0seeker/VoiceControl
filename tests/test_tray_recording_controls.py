from __future__ import annotations

import threading
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from voicecontrol import tray_app
from voicecontrol.control.commands import PAUSE_LISTENING, RELOAD_EXECUTOR, RESUME_LISTENING
from voicecontrol.events.status import StatusPublisher, StatusType
from voicecontrol.events.status_snapshot import RuntimeStatusSnapshotStore, read_runtime_status


class TrayRecordingControlTests(unittest.TestCase):
    def _app(self) -> tray_app.TrayApp:
        app = tray_app.TrayApp.__new__(tray_app.TrayApp)
        app._manual_record_event = threading.Event()
        app._recording_stop_event = threading.Event()
        app._is_recording = False
        app._icon = Mock()
        app._status_unsubscribe = None
        app._orchestrator = None
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

    def test_control_command_pause_and_resume_update_listening_state(self) -> None:
        app = self._app()
        app._paused = threading.Event()

        app._handle_control_command(PAUSE_LISTENING)
        self.assertTrue(app._paused.is_set())

        app._handle_control_command(RESUME_LISTENING)
        self.assertFalse(app._paused.is_set())

    def test_pause_and_resume_commands_write_runtime_status_snapshot(self) -> None:
        app = self._app()
        app._paused = threading.Event()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "runtime_status.json"
            app._status_snapshot_store = RuntimeStatusSnapshotStore(path=path)

            app._handle_control_command(PAUSE_LISTENING)
            paused_snapshot = read_runtime_status(path)
            app._handle_control_command(RESUME_LISTENING)
            resumed_snapshot = read_runtime_status(path)

        self.assertIsNotNone(paused_snapshot)
        self.assertIsNotNone(resumed_snapshot)
        assert paused_snapshot is not None
        assert resumed_snapshot is not None
        self.assertEqual(paused_snapshot.current, "paused")
        self.assertEqual(resumed_snapshot.current, "listening")

    def test_reload_executor_command_writes_success_response(self) -> None:
        app = self._app()
        app._orchestrator = Mock()
        app._orchestrator.driver.app_name = "Trae"

        with patch("voicecontrol.tray_app.write_control_response") as write_response:
            app._handle_control_command(RELOAD_EXECUTOR)

        app._orchestrator.reload_driver.assert_called_once_with()
        write_response.assert_called_once_with(RELOAD_EXECUTOR, "ok", "Executor target switched to: Trae")

    def test_reload_executor_command_reports_missing_orchestrator(self) -> None:
        app = self._app()

        with patch("voicecontrol.tray_app.write_control_response") as write_response:
            app._handle_control_command(RELOAD_EXECUTOR)

        write_response.assert_called_once_with(
            RELOAD_EXECUTOR,
            "error",
            "Wake loop is not ready; executor was not reloaded.",
        )

    def test_control_worker_dispatches_pause_command(self) -> None:
        app = self._app()
        app._paused = threading.Event()
        app._stop_event = Mock()
        app._stop_event.is_set.side_effect = [False, True]

        with patch("voicecontrol.tray_app.read_control_command", return_value=PAUSE_LISTENING):
            app._control_worker()

        self.assertTrue(app._paused.is_set())
        app._icon.update_menu.assert_called_once()

    def test_status_events_update_tray_recording_state_and_title(self) -> None:
        app = self._app()
        publisher = StatusPublisher()

        app._subscribe_status_events(publisher)
        publisher.publish(StatusType.RECORDING)

        self.assertTrue(app._is_recording)
        self.assertIn("VoiceControl", app._icon.title)
        app._icon.update_menu.assert_called_once()

        publisher.publish(StatusType.TRANSCRIBING)

        self.assertFalse(app._is_recording)

    def test_status_events_write_runtime_status_snapshot(self) -> None:
        app = self._app()
        publisher = StatusPublisher()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "runtime_status.json"
            app._status_snapshot_store = RuntimeStatusSnapshotStore(path=path)

            app._subscribe_status_events(publisher)
            publisher.publish(StatusType.RECORDING, message="recording now")

            snapshot = read_runtime_status(path)

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(snapshot.current, "recording")
        self.assertEqual(snapshot.message, "recording now")

    def test_status_event_subscription_can_be_closed(self) -> None:
        app = self._app()
        publisher = StatusPublisher()
        app._subscribe_status_events(publisher)

        app._close_status_subscription()
        publisher.publish(StatusType.RECORDING)

        self.assertFalse(app._is_recording)


if __name__ == "__main__":
    unittest.main()
