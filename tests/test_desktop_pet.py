from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from voicecontrol.events.status_snapshot import RuntimeStatusSnapshot, write_runtime_status
from voicecontrol.ui.desktop_pet import DesktopPetWindow, pet_state_from_snapshot


class DesktopPetStateTests(unittest.TestCase):
    def test_runtime_status_maps_to_pet_expression_and_text(self) -> None:
        cases = [
            ("listening", ":)", "监听中"),
            ("recording", "REC", "录音中"),
            ("sending", ">>", "发送中"),
            ("error", "!", "出错"),
        ]

        for current, expression, text in cases:
            with self.subTest(current=current):
                state = pet_state_from_snapshot(
                    RuntimeStatusSnapshot(current=current, message="window not found")
                )

                self.assertEqual(state.expression, expression)
                self.assertEqual(state.text, text)

    def test_missing_runtime_status_uses_standby_state(self) -> None:
        state = pet_state_from_snapshot(None)

        self.assertEqual(state.expression, "...")
        self.assertEqual(state.text, "待命")


class DesktopPetWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_pet_window_is_transparent_topmost_tool_window(self) -> None:
        window = DesktopPetWindow()

        flags = window.windowFlags()

        self.assertTrue(flags & Qt.WindowType.FramelessWindowHint)
        self.assertTrue(flags & Qt.WindowType.WindowStaysOnTopHint)
        self.assertTrue(flags & Qt.WindowType.Tool)
        self.assertTrue(window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        self.assertEqual(window.objectName(), "desktopPetWindow")

    def test_pet_window_context_menu_exposes_open_and_quit_actions(self) -> None:
        window = DesktopPetWindow()

        menu = window._build_context_menu()
        action_texts = [action.text() for action in menu.actions()]

        self.assertEqual(["打开控制中心", "退出桌宠"], action_texts)

    def test_left_click_opens_control_center_when_not_dragged(self) -> None:
        launcher = Mock()
        window = DesktopPetWindow(open_control_center=launcher)

        window._handle_pet_clicked()

        launcher.assert_called_once_with()

    def test_pet_window_refreshes_from_runtime_status_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            status_path = Path(temp_dir) / "runtime_status.json"
            write_runtime_status(
                RuntimeStatusSnapshot(
                    current="recording",
                    message="recording now",
                    is_recording=True,
                    updated_at=datetime(2026, 6, 27, 9, 30, 0),
                ),
                path=status_path,
            )
            window = DesktopPetWindow(runtime_status_path=status_path)

            expression = window.findChild(QLabel, "petExpressionLabel")
            status = window.findChild(QLabel, "petStatusLabel")

            self.assertEqual(expression.text(), "REC")
            self.assertEqual(status.text(), "录音中")


if __name__ == "__main__":
    unittest.main()
