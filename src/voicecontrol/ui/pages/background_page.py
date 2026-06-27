"""Background control page for the VoiceControl settings UI."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from voicecontrol.config import settings
from voicecontrol.control.commands import (
    PAUSE_LISTENING,
    RESUME_LISTENING,
    write_control_command,
)
from voicecontrol.ui.pages.base import page_layout
from voicecontrol.ui.widgets import card, switch


class BackgroundControlPage(QWidget):
    """Controls the tray daemon and runs lightweight smoke tests."""

    def __init__(
        self,
        config: dict | None = None,
        log_path: Path | None = None,
        command_history_path: Path | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("backgroundControlPage")
        self._config = config or {}
        self._log_path = log_path
        self._command_history_path = command_history_path

        root_layout = page_layout(self, "后台控制", "控制托盘监听流程并运行轻量测试。")
        root_layout.setSpacing(16)
        self._result_label = QLabel("尚未执行。")
        self._result_label.setObjectName("backgroundControlResultLabel")
        self._result_label.setWordWrap(True)

        self._add_listening_card(root_layout)
        self._add_location_card(root_layout)
        root_layout.addWidget(self._result_label)
        root_layout.addStretch(1)

    def _add_listening_card(self, root_layout: QVBoxLayout) -> None:
        frame, layout = card("监听")
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        label = QLabel("托盘监听")
        label.setObjectName("fieldLabel")
        self._listening_switch = switch(True)
        self._listening_switch.setObjectName("listeningControlSwitch")
        self._listening_switch.toggled.connect(self._toggle_listening)

        row.addWidget(label, 1)
        row.addWidget(self._listening_switch, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(row)
        root_layout.addWidget(frame)

    def _add_location_card(self, root_layout: QVBoxLayout) -> None:
        frame, layout = card("文件位置")
        row, row_layout = self._action_row("backgroundLocationActions")
        row_layout.addWidget(
            self._button(
                "打开日志位置",
                "openLogsLocationButton",
                lambda: self._open_location(self._log_path or settings.log_file_path()),
            )
        )
        row_layout.addWidget(
            self._button(
                "打开历史位置",
                "openHistoryLocationButton",
                lambda: self._open_location(
                    self._command_history_path or settings.COMMAND_HISTORY_PATH
                ),
            )
        )
        row_layout.addStretch(1)
        layout.addWidget(row)
        root_layout.addWidget(frame)

    def _action_row(self, object_name: str) -> tuple[QWidget, QHBoxLayout]:
        row = QWidget()
        row.setObjectName(object_name)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        return row, layout

    def _button(self, label: str, object_name: str, handler) -> QPushButton:  # noqa: ANN001
        button = QPushButton(label)
        button.setObjectName(object_name)
        button.clicked.connect(handler)
        return button

    def _toggle_listening(self, enabled: bool) -> None:
        if enabled:
            self._send_control_command(RESUME_LISTENING, "已请求恢复监听。")
        else:
            self._send_control_command(PAUSE_LISTENING, "已请求暂停监听。")

    def _send_control_command(self, command: str, success_message: str) -> None:
        try:
            write_control_command(command)
        except Exception as exc:
            self._result_label.setText(f"失败：{exc}")
            return
        self._result_label.setText(success_message)

    def _open_location(self, path: Path) -> None:
        directory = path if path.is_dir() else path.parent
        try:
            directory.mkdir(parents=True, exist_ok=True)
            os.startfile(str(directory))
        except OSError as exc:
            self._result_label.setText(f"打开位置失败：{exc}")
            return
        self._result_label.setText(f"已打开：{directory}")
