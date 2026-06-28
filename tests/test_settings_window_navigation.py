from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QWidget,
)

from voicecontrol.config.manager import load_config
from voicecontrol.control.commands import PAUSE_LISTENING, RESUME_LISTENING, START_RECORDING, STOP_RECORDING
from voicecontrol.diagnostics.store import DiagnosticResult
from voicecontrol.events.status import StatusPublisher, StatusType
from voicecontrol.events.status_snapshot import RuntimeStatusSnapshot, write_runtime_status
from voicecontrol.history.resend import ResendResult
from voicecontrol.history.store import CommandHistoryRecord, append_command_history
from voicecontrol.ui.config_binding import set_nested
from voicecontrol.ui.pages.logs_page import LogsPage
from voicecontrol.ui.settings_window import SettingsWindow
from voicecontrol.ui.style import apple_style_sheet


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
        self.assertEqual(recording_button.text(), "录音")
        self.assertEqual(stack.currentWidget(), recording_page)

        settings_button.click()

        self.assertEqual(stack.currentWidget(), settings_page)

    def test_window_exposes_control_center_navigation_pages(self) -> None:
        window = SettingsWindow(load_config())
        stack = window.findChild(QStackedWidget, "pageStack")

        pages = [
            ("navRecording", "recordingPage"),
            ("navSettings", "settingsPage"),
            ("navDiagnostics", "diagnosticsPage"),
            ("navCommandHistory", "commandHistoryPage"),
            ("navLogs", "logsPage"),
        ]

        self.assertIsNotNone(stack)
        for nav_name, page_name in pages:
            with self.subTest(nav=nav_name, page=page_name):
                button = window.findChild(QPushButton, nav_name)
                page = window.findChild(QWidget, page_name)

                self.assertIsNotNone(button)
                self.assertIsNotNone(page)

                button.click()

                self.assertEqual(stack.currentWidget(), page)
                self.assertTrue(button.isChecked())

        self.assertIsNone(window.findChild(QPushButton, "navMicrophoneDiagnostics"))
        self.assertIsNone(window.findChild(QPushButton, "navVadTest"))
        self.assertIsNone(window.findChild(QPushButton, "navWakeWordTest"))
        self.assertIsNone(window.findChild(QPushButton, "navTts"))
        self.assertIsNone(window.findChild(QWidget, "ttsPage"))
        self.assertIsNone(window.findChild(QPushButton, "navStatus"))
        self.assertIsNone(window.findChild(QWidget, "statusPage"))
        self.assertIsNone(window.findChild(QPushButton, "navBackgroundControl"))
        self.assertIsNone(window.findChild(QWidget, "backgroundControlPage"))

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

        target = window.findChild(QComboBox, "executorTargetCombo")
        self.assertIsNotNone(target)

    def test_settings_page_exposes_executor_target_selector(self) -> None:
        window = SettingsWindow(load_config())
        target = window.findChild(QComboBox, "executorTargetCombo")

        self.assertIsNotNone(target)
        self.assertEqual(target.currentText(), "cursor")
        self.assertEqual([target.itemText(index) for index in range(target.count())], ["codex", "chatgpt", "cursor", "trae"])

    def test_settings_page_binds_trae_composer_coordinates(self) -> None:
        from PySide6.QtWidgets import QDoubleSpinBox

        config = load_config()
        config["executor"]["default_target"] = "trae"
        config["executor"]["trae_composer_click_rel_x"] = 0.33
        config["executor"]["trae_composer_click_rel_y"] = 0.44
        window = SettingsWindow(config)

        click_x = window.findChild(QDoubleSpinBox, "traeComposerClickRelX")
        click_y = window.findChild(QDoubleSpinBox, "traeComposerClickRelY")

        self.assertIsNotNone(click_x)
        self.assertIsNotNone(click_y)
        self.assertAlmostEqual(click_x.value(), 0.33)
        self.assertAlmostEqual(click_y.value(), 0.44)

        click_x.setValue(0.66)
        click_y.setValue(0.77)
        next_config = load_config()
        settings_page = window.findChild(QWidget, "settingsPage")
        self.assertIsNotNone(settings_page)
        for path, reader in settings_page._bindings:
            set_nested(next_config, path, reader())

        self.assertAlmostEqual(next_config["executor"]["trae_composer_click_rel_x"], 0.66)
        self.assertAlmostEqual(next_config["executor"]["trae_composer_click_rel_y"], 0.77)

    def test_settings_page_hides_cursor_composer_coordinates(self) -> None:
        from PySide6.QtWidgets import QDoubleSpinBox

        config = load_config()
        config["executor"]["default_target"] = "cursor"
        config["executor"]["cursor_composer_click_rel_x"] = 0.83
        config["executor"]["cursor_composer_click_rel_y"] = 0.97
        window = SettingsWindow(config)

        click_x = window.findChild(QDoubleSpinBox, "cursorComposerClickRelX")
        click_y = window.findChild(QDoubleSpinBox, "cursorComposerClickRelY")

        self.assertIsNone(click_x)
        self.assertIsNone(click_y)

    def test_apply_executor_change_waits_for_reload_ack(self) -> None:
        window = SettingsWindow(load_config())
        apply_button = window.findChild(QPushButton, "applyExecutorChangeButton")

        self.assertIsNotNone(apply_button)
        with (
            patch("voicecontrol.ui.pages.settings_page.write_control_command") as write_command,
            patch("voicecontrol.ui.pages.settings_page.read_control_response") as read_response,
            patch("voicecontrol.ui.pages.settings_page.QMessageBox.information") as information,
        ):
            read_response.return_value = {
                "command": "reload_executor",
                "status": "ok",
                "message": "Executor target switched to: Trae",
                "created_at": 9999999999.0,
            }
            apply_button.click()

        write_command.assert_called_once_with("reload_executor")
        information.assert_called_once()
        self.assertIn("Executor target switched to: Trae", information.call_args.args[2])

    def test_settings_page_exposes_tts_controls(self) -> None:
        window = SettingsWindow(load_config())

        self.assertIsNotNone(window.findChild(QWidget, "ttsEnabled"))
        self.assertIsNotNone(window.findChild(QWidget, "ttsRate"))
        self.assertIsNotNone(window.findChild(QWidget, "ttsVolume"))
        self.assertIsNotNone(window.findChild(QLineEdit, "ttsVoice"))
        self.assertIsNotNone(window.findChild(QPushButton, "testTtsButton"))

    def test_settings_page_exposes_desktop_pet_controls(self) -> None:
        window = SettingsWindow(load_config())

        self.assertIsNotNone(window.findChild(QWidget, "desktopPetAnimationEnabled"))

    def test_tts_test_button_speaks_sample_phrase(self) -> None:
        window = SettingsWindow(load_config())
        button = window.findChild(QPushButton, "testTtsButton")

        with patch("voicecontrol.ui.pages.settings_page.TextSpeaker") as speaker_class:
            button.click()

        speaker_class.return_value.speak.assert_called_once_with("我在")

    def test_status_page_updates_from_injected_status_publisher(self) -> None:
        publisher = StatusPublisher()
        window = SettingsWindow(load_config(), status_publisher=publisher)

        current = window.findChild(QLabel, "currentStatusLabel")
        recent = window.findChild(QLabel, "recentStatusEventsLabel")
        recording = window.findChild(QLabel, "isRecordingLabel")
        sending = window.findChild(QLabel, "isSendingLabel")
        error = window.findChild(QLabel, "lastErrorLabel")

        publisher.publish(StatusType.RECORDING, message="recording now")

        self.assertIn("recording", current.text())
        self.assertIn("是", recording.text())

        publisher.publish(StatusType.SENDING, message="sending to Codex")

        self.assertIn("sending", current.text())
        self.assertIn("否", recording.text())
        self.assertIn("是", sending.text())

        publisher.publish(StatusType.ERROR, message="window not found")

        self.assertIn("error", current.text())
        self.assertIn("recording now", recent.text())
        self.assertIn("sending to Codex", recent.text())
        self.assertIn("window not found", recent.text())
        self.assertIn("window not found", error.text())

    def test_status_page_polls_runtime_status_snapshot_every_second(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            status_path = Path(temp_dir) / "runtime_status.json"
            write_runtime_status(
                RuntimeStatusSnapshot(
                    current="recording",
                    message="recording now",
                    is_recording=True,
                    recent_events=[{"type": "recording", "message": "recording now", "created_at": "09:30:00"}],
                ),
                path=status_path,
            )
            window = SettingsWindow(load_config(), runtime_status_path=status_path)

            timer = window.findChild(QTimer, "runtimeStatusPollTimer")
            current = window.findChild(QLabel, "currentStatusLabel")
            recent = window.findChild(QLabel, "recentStatusEventsLabel")

            self.assertIsNotNone(timer)
            self.assertEqual(timer.interval(), 1000)
            self.assertIn("recording", current.text())
            self.assertIn("recording now", recent.text())

            write_runtime_status(
                RuntimeStatusSnapshot(
                    current="sending",
                    message="sending to Codex",
                    is_sending=True,
                    recent_events=[{"type": "sending", "message": "sending to Codex", "created_at": "09:31:00"}],
                ),
                path=status_path,
            )
            timer.timeout.emit()

            self.assertIn("sending", current.text())
            self.assertIn("sending to Codex", recent.text())

    def test_status_page_shows_runtime_updated_time_and_missing_file_hint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            status_path = Path(temp_dir) / "runtime_status.json"
            write_runtime_status(
                RuntimeStatusSnapshot(
                    current="idle",
                    message="ready",
                    updated_at=datetime(2026, 6, 27, 9, 30, 0),
                ),
                path=status_path,
            )

            window = SettingsWindow(load_config(), runtime_status_path=status_path)
            updated_at = window.findChild(QLabel, "runtimeStatusUpdatedAtLabel")
            hint = window.findChild(QLabel, "runtimeStatusHintLabel")

            self.assertIsNotNone(updated_at)
            self.assertIsNotNone(hint)
            self.assertIn("2026-06-27 09:30:00", updated_at.text())
            self.assertEqual("", hint.text())

            missing_path = Path(temp_dir) / "missing_runtime_status.json"
            missing_window = SettingsWindow(load_config(), runtime_status_path=missing_path)
            missing_hint = missing_window.findChild(QLabel, "runtimeStatusHintLabel")

            self.assertIsNotNone(missing_hint)
            self.assertIn("托盘未运行", missing_hint.text())
            self.assertIn("状态文件不存在", missing_hint.text())

    def test_status_page_contains_runtime_controls(self) -> None:
        window = SettingsWindow(load_config())

        self.assertIsNotNone(window.findChild(QCheckBox, "listeningControlSwitch"))
        self.assertIsNotNone(window.findChild(QPushButton, "statusStartRecordingButton"))
        self.assertIsNotNone(window.findChild(QPushButton, "statusStopRecordingButton"))
        self.assertIsNotNone(window.findChild(QLabel, "statusControlResultLabel"))

    def test_recording_page_uses_scroll_area_for_long_status_text(self) -> None:
        window = SettingsWindow(load_config())
        scroll = window.findChild(QScrollArea, "recordingScrollArea")

        self.assertIsNotNone(scroll)
        self.assertTrue(scroll.widgetResizable())

    def test_status_and_diagnostic_result_text_can_be_selected_for_copying(self) -> None:
        window = SettingsWindow(load_config())
        selectable_labels = [
            "statusControlResultLabel",
            "currentStatusLabel",
            "isRecordingLabel",
            "isSendingLabel",
            "lastErrorLabel",
            "runtimeStatusUpdatedAtLabel",
            "runtimeStatusHintLabel",
            "recentStatusEventsLabel",
            "microphoneDiagnosticResultLabel",
            "vadTestResultLabel",
            "wakeWordTestResultLabel",
            "ttsDiagnosticResultLabel",
            "codexSendDiagnosticResultLabel",
        ]

        for object_name in selectable_labels:
            with self.subTest(label=object_name):
                label = window.findChild(QLabel, object_name)

                self.assertIsNotNone(label)
                self.assertTrue(
                    label.textInteractionFlags()
                    & Qt.TextInteractionFlag.TextSelectableByMouse
                )

    def test_status_page_runtime_controls_write_tray_commands(self) -> None:
        window = SettingsWindow(load_config())
        listening_switch = window.findChild(QCheckBox, "listeningControlSwitch")
        start = window.findChild(QPushButton, "statusStartRecordingButton")
        stop = window.findChild(QPushButton, "statusStopRecordingButton")

        with patch("voicecontrol.ui.pages.status_page.write_control_command") as write_command:
            listening_switch.setChecked(False)
            listening_switch.setChecked(True)
            start.click()
            stop.click()

        self.assertEqual(
            [call.args[0] for call in write_command.call_args_list],
            [PAUSE_LISTENING, RESUME_LISTENING, START_RECORDING, STOP_RECORDING],
        )

    def test_command_history_page_loads_records_and_refreshes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "command_history.jsonl"
            append_command_history(
                CommandHistoryRecord(
                    text="打开项目",
                    wav_path=Path("audio_files/one.wav"),
                    sent=True,
                    created_at=datetime(2026, 6, 27, 9, 30, 0),
                ),
                path=history_path,
            )
            window = SettingsWindow(load_config(), command_history_path=history_path)
            table = window.findChild(QTableWidget, "commandHistoryTable")
            refresh = window.findChild(QPushButton, "refreshCommandHistoryButton")

            self.assertEqual(table.rowCount(), 1)
            self.assertEqual(table.item(0, 1).text(), "打开项目")
            self.assertEqual(table.item(0, 3).text(), "是")

            append_command_history(
                CommandHistoryRecord(
                    text="失败命令",
                    wav_path=Path("audio_files/two.wav"),
                    sent=False,
                    send_error="Codex window not found",
                    error="send failed",
                    created_at=datetime(2026, 6, 27, 9, 31, 0),
                ),
                path=history_path,
            )

            refresh.click()

            self.assertEqual(table.rowCount(), 2)
            self.assertEqual(table.item(1, 1).text(), "失败命令")
            self.assertEqual(table.item(1, 3).text(), "否")
            self.assertEqual(table.item(1, 4).text(), "Codex window not found")
            self.assertEqual(table.item(1, 5).text(), "send failed")

    def test_command_history_page_resends_last_command_and_shows_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "command_history.jsonl"
            window = SettingsWindow(load_config(), command_history_path=history_path)
            button = window.findChild(QPushButton, "resendLastCommandButton")
            result = window.findChild(QLabel, "resendLastCommandResultLabel")

            with patch("voicecontrol.ui.pages.command_history_page.resend_last_command") as resend:
                resend.return_value = ResendResult(text="打开项目", sent=True)
                button.click()

            resend.assert_called_once_with(history_path=history_path)
            self.assertIn("已重发", result.text())
            self.assertIn("打开项目", result.text())

    def test_command_history_page_shows_resend_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "command_history.jsonl"
            window = SettingsWindow(load_config(), command_history_path=history_path)
            button = window.findChild(QPushButton, "resendLastCommandButton")
            result = window.findChild(QLabel, "resendLastCommandResultLabel")

            with patch("voicecontrol.ui.pages.command_history_page.resend_last_command") as resend:
                resend.return_value = ResendResult(text="打开项目", sent=False, send_error="Codex window not found")
                button.click()

            self.assertIn("重发失败", result.text())
            self.assertIn("Codex window not found", result.text())

    def test_logs_page_shows_recent_log_lines_and_refreshes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "voicecontrol.log"
            log_path.write_text("first\nsecond\n", encoding="utf-8")
            window = SettingsWindow(load_config(), log_path=log_path)
            text = window.findChild(QPlainTextEdit, "recentLogLinesText")
            refresh = window.findChild(QPushButton, "refreshLogsButton")

            self.assertIn("first", text.toPlainText())
            self.assertIn("second", text.toPlainText())

            log_path.write_text("third\nfourth\n", encoding="utf-8")
            refresh.click()

            self.assertNotIn("first", text.toPlainText())
            self.assertIn("third", text.toPlainText())
            self.assertIn("fourth", text.toPlainText())

    def test_logs_page_shows_empty_state_for_missing_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "missing.log"
            window = SettingsWindow(load_config(), log_path=log_path)
            text = window.findChild(QPlainTextEdit, "recentLogLinesText")

            self.assertIn("暂无日志", text.toPlainText())

    def test_logs_page_opens_log_location(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "voicecontrol.log"
            window = SettingsWindow(load_config(), log_path=log_path)
            button = window.findChild(QPushButton, "openLogsLocationButton")

            with patch("voicecontrol.ui.pages.logs_page.os.startfile") as startfile:
                button.click()

            startfile.assert_called_once_with(str(log_path.parent))

    def test_logs_page_keeps_space_between_refresh_button_and_log_content(self) -> None:
        page = LogsPage()
        layout = page.layout()

        self.assertIsNotNone(layout.itemAt(3).spacerItem())
        self.assertGreaterEqual(layout.itemAt(3).spacerItem().sizeHint().height(), 16)

    def test_primary_buttons_use_black_pill_style(self) -> None:
        sheet = apple_style_sheet()

        self.assertIn("QPushButton {", sheet)
        self.assertIn("background: #1d1d1f;", sheet)
        self.assertIn("min-height: 36px;", sheet)
        self.assertIn("border-radius: 18px;", sheet)
        self.assertNotIn("background: #007aff;", sheet)
        self.assertNotIn("background: #0a84ff;", sheet)
        self.assertNotIn("background: #0066d6;", sheet)

    def test_diagnostic_pages_call_services_and_show_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostic_path = Path(temp_dir) / "diagnostics.jsonl"
            window = SettingsWindow(load_config(), diagnostic_path=diagnostic_path)

            mic_button = window.findChild(QPushButton, "runMicrophoneDiagnosticButton")
            mic_result = window.findChild(QLabel, "microphoneDiagnosticResultLabel")
            vad_path = window.findChild(QLineEdit, "vadTestFilePath")
            vad_button = window.findChild(QPushButton, "runVadTestButton")
            vad_result = window.findChild(QLabel, "vadTestResultLabel")
            wake_path = window.findChild(QLineEdit, "wakeWordTestFilePath")
            wake_button = window.findChild(QPushButton, "runWakeWordTestButton")
            wake_result = window.findChild(QLabel, "wakeWordTestResultLabel")
            tts_button = window.findChild(QPushButton, "backgroundTestTtsButton")
            tts_result = window.findChild(QLabel, "ttsDiagnosticResultLabel")
            codex_button = window.findChild(QPushButton, "testSendToCodexButton")
            codex_result = window.findChild(QLabel, "codexSendDiagnosticResultLabel")

            with (
                patch("voicecontrol.ui.pages.diagnostics_page.run_microphone_test") as microphone,
                patch("voicecontrol.ui.pages.diagnostics_page.run_vad_file_test") as vad,
                patch("voicecontrol.ui.pages.diagnostics_page.run_wake_word_file_test") as wake_word,
                patch("voicecontrol.ui.pages.diagnostics_page.TextSpeaker") as speaker_class,
                patch("voicecontrol.ui.pages.diagnostics_page.get_default_driver") as get_default_driver,
            ):
                microphone.return_value = DiagnosticResult(name="microphone", status="ok", details={"rms": 0.25})
                vad.return_value = DiagnosticResult(name="vad", status="ok", details={"finished": True})
                wake_word.return_value = DiagnosticResult(
                    name="wake_word",
                    status="ok",
                    details={"max_score": 0.8, "detected": True},
                )

                mic_button.click()
                vad_path.setText("sample_vad.wav")
                vad_button.click()
                wake_path.setText("sample_wake.wav")
                wake_button.click()
                tts_button.click()
                codex_button.click()

            microphone.assert_called_once_with(diagnostic_path=diagnostic_path)
            vad.assert_called_once_with("sample_vad.wav", diagnostic_path=diagnostic_path)
            wake_word.assert_called_once_with("sample_wake.wav", diagnostic_path=diagnostic_path)
            speaker_class.return_value.speak.assert_called_once()
            get_default_driver.return_value.send_prompt.assert_called_once()
            self.assertIn("ok", mic_result.text())
            self.assertIn("rms", mic_result.text())
            self.assertIn("ok", vad_result.text())
            self.assertIn("finished", vad_result.text())
            self.assertIn("ok", wake_result.text())
            self.assertIn("max_score", wake_result.text())
            self.assertIn("TTS", tts_result.text())
            self.assertIn("发送", codex_result.text())

    def test_diagnostic_page_shows_failure_result(self) -> None:
        window = SettingsWindow(load_config())
        mic_button = window.findChild(QPushButton, "runMicrophoneDiagnosticButton")
        mic_result = window.findChild(QLabel, "microphoneDiagnosticResultLabel")

        with patch("voicecontrol.ui.pages.diagnostics_page.run_microphone_test") as microphone:
            microphone.return_value = DiagnosticResult(name="microphone", status="error", error="mic unavailable")
            mic_button.click()

        self.assertIn("error", mic_result.text())
        self.assertIn("mic unavailable", mic_result.text())

    def test_diagnostic_button_shows_busy_state_while_running(self) -> None:
        window = SettingsWindow(load_config())
        mic_button = window.findChild(QPushButton, "runMicrophoneDiagnosticButton")
        mic_result = window.findChild(QLabel, "microphoneDiagnosticResultLabel")

        def run_slow_diagnostic(*, diagnostic_path: Path | None = None) -> DiagnosticResult:
            self.assertFalse(mic_button.isEnabled())
            self.assertIn("运行中", mic_result.text())
            return DiagnosticResult(name="microphone", status="ok")

        with patch("voicecontrol.ui.pages.diagnostics_page.run_microphone_test") as microphone:
            microphone.side_effect = run_slow_diagnostic
            mic_button.click()

        self.assertTrue(mic_button.isEnabled())
        self.assertIn("ok", mic_result.text())

    def test_diagnostic_button_shows_service_exception(self) -> None:
        window = SettingsWindow(load_config())
        mic_button = window.findChild(QPushButton, "runMicrophoneDiagnosticButton")
        mic_result = window.findChild(QLabel, "microphoneDiagnosticResultLabel")

        with patch("voicecontrol.ui.pages.diagnostics_page.run_microphone_test") as microphone:
            microphone.side_effect = RuntimeError("mic unavailable")
            mic_button.click()

        self.assertTrue(mic_button.isEnabled())
        self.assertIn("error", mic_result.text())
        self.assertIn("mic unavailable", mic_result.text())

    def test_diagnostics_page_keeps_space_between_cards(self) -> None:
        window = SettingsWindow(load_config())
        page = window.findChild(QWidget, "diagnosticsPage")

        self.assertIsNotNone(page)
        self.assertGreaterEqual(page.layout().spacing(), 14)

    def test_diagnostics_page_uses_scroll_area_for_long_test_list(self) -> None:
        window = SettingsWindow(load_config())
        scroll = window.findChild(QScrollArea, "diagnosticsScrollArea")

        self.assertIsNotNone(scroll)
        self.assertTrue(scroll.widgetResizable())

    def test_command_history_page_opens_history_location(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "command_history.jsonl"
            window = SettingsWindow(load_config(), command_history_path=history_path)
            button = window.findChild(QPushButton, "openHistoryLocationButton")

            with patch("voicecontrol.ui.pages.command_history_page.os.startfile") as startfile:
                button.click()

            startfile.assert_called_once_with(str(history_path.parent))


if __name__ == "__main__":
    unittest.main()

