"""Log viewer page for the VoiceControl settings UI."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from voicecontrol.config import settings
from voicecontrol.diagnostics.logs import read_recent_log_lines


class LogsPage(QWidget):
    """Page that shows the tail of the current day's tray log file."""

    def __init__(self, log_path: Path | None = None) -> None:
        super().__init__()
        self.setObjectName("logsPage")
        self._log_path = log_path

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 30, 36, 28)
        root_layout.setSpacing(0)

        title = QLabel("日志查看")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        root_layout.addWidget(title)

        subtitle = QLabel("查看最近的后台运行日志。")
        subtitle.setObjectName("subtitle")
        root_layout.addWidget(subtitle)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("refreshLogsButton")
        open_button = QPushButton("打开日志位置")
        open_button.setObjectName("openLogsLocationButton")

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(12)
        actions.addStretch(1)
        actions.addWidget(open_button)
        actions.addWidget(refresh_button)
        root_layout.addLayout(actions)
        root_layout.addSpacing(18)

        self._recent_log_lines_text = QPlainTextEdit()
        self._recent_log_lines_text.setObjectName("recentLogLinesText")
        self._recent_log_lines_text.setReadOnly(True)
        root_layout.addWidget(self._recent_log_lines_text, 1)

        refresh_button.clicked.connect(self._load_recent_logs)
        open_button.clicked.connect(self._open_log_location)
        self._load_recent_logs()

    def _load_recent_logs(self) -> None:
        lines = read_recent_log_lines(path=self._log_path)
        self._recent_log_lines_text.setPlainText("\n".join(lines) if lines else "暂无日志。")

    def _open_log_location(self) -> None:
        path = self._log_path or settings.log_file_path()
        directory = path if path.is_dir() else path.parent
        directory.mkdir(parents=True, exist_ok=True)
        os.startfile(str(directory))
