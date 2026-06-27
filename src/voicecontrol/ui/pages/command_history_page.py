"""Command history page for the VoiceControl settings UI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from voicecontrol.history.resend import ResendError, resend_last_command
from voicecontrol.history.store import read_command_history


class CommandHistoryPage(QWidget):
    """Page listing recent voice commands with a re-send action."""

    def __init__(self, command_history_path: Path | None = None) -> None:
        super().__init__()
        self.setObjectName("commandHistoryPage")
        self._command_history_path = command_history_path

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 30, 36, 28)
        root_layout.setSpacing(0)

        title = QLabel("命令历史")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        root_layout.addWidget(title)

        subtitle = QLabel("查看最近的语音命令、录音文件和发送结果。")
        subtitle.setObjectName("subtitle")
        root_layout.addWidget(subtitle)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("refreshCommandHistoryButton")
        resend_button = QPushButton("重发上一条")
        resend_button.setObjectName("resendLastCommandButton")

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 12)
        actions.setSpacing(12)
        actions.addStretch(1)
        actions.addWidget(resend_button)
        actions.addWidget(refresh_button)
        root_layout.addLayout(actions)

        self._resend_last_command_result_label = QLabel("")
        self._resend_last_command_result_label.setObjectName("resendLastCommandResultLabel")
        self._resend_last_command_result_label.setWordWrap(True)
        root_layout.addWidget(self._resend_last_command_result_label)

        self._command_history_table = QTableWidget(0, 6)
        self._command_history_table.setObjectName("commandHistoryTable")
        self._command_history_table.setHorizontalHeaderLabels(
            ["时间", "文本", "WAV", "已发送", "发送错误", "错误"]
        )
        self._command_history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._command_history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._command_history_table.horizontalHeader().setStretchLastSection(True)
        root_layout.addWidget(self._command_history_table, 1)

        refresh_button.clicked.connect(self._load_command_history)
        resend_button.clicked.connect(self._resend_last_command)
        self._load_command_history()

    def _load_command_history(self) -> None:
        records = read_command_history(path=self._command_history_path)
        self._command_history_table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                record.created_at.isoformat(timespec="seconds"),
                record.text,
                record.wav_path.as_posix(),
                "是" if record.sent else "否",
                record.send_error or "",
                record.error or "",
            ]
            for column, value in enumerate(values):
                self._command_history_table.setItem(row, column, QTableWidgetItem(value))
        self._command_history_table.resizeColumnsToContents()

    def _resend_last_command(self) -> None:
        try:
            result = resend_last_command(history_path=self._command_history_path)
        except ResendError as exc:
            self._resend_last_command_result_label.setText(f"重发失败：{exc}")
            return

        if result.sent:
            self._resend_last_command_result_label.setText(f"已重发：{result.text}")
        else:
            self._resend_last_command_result_label.setText(
                f"重发失败：{result.send_error or '未知错误'}"
            )
        self._load_command_history()
