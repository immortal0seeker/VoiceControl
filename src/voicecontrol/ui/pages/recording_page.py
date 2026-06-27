"""Recording control page for the VoiceControl settings UI."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from voicecontrol.control.commands import START_RECORDING, STOP_RECORDING, write_control_command
from voicecontrol.ui.widgets import card


class RecordingPage(QWidget):
    """Page for starting and stopping tray-daemon recording via file commands."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("recordingPage")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 30, 36, 28)
        root_layout.setSpacing(0)

        title = QLabel("Recording")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        root_layout.addWidget(title)

        subtitle = QLabel("控制托盘后台的录音流程。")
        subtitle.setObjectName("subtitle")
        root_layout.addWidget(subtitle)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)
        self._add_recording_control_card(content_layout)
        content_layout.addStretch(1)
        root_layout.addWidget(content, 1)

    def _add_recording_control_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Recording")
        start_button = QPushButton("开始录音")
        stop_button = QPushButton("停止录音")
        stop_button.setObjectName("secondary")

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(14)
        controls.addWidget(start_button)
        controls.addWidget(stop_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        start_button.clicked.connect(self._request_start_recording)
        stop_button.clicked.connect(self._request_stop_recording)
        content_layout.addWidget(frame)

    def _request_start_recording(self) -> None:
        write_control_command(START_RECORDING)
        QMessageBox.information(self, "已发送", "已请求托盘后台开始录音。")

    def _request_stop_recording(self) -> None:
        write_control_command(STOP_RECORDING)
        QMessageBox.information(self, "已发送", "已请求托盘后台停止录音。")
