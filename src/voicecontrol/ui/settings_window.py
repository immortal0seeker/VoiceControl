"""Settings window navigation shell.

Assembles the sidebar navigation and QStackedWidget from individual page
modules.  All business logic lives in the page classes under ui/pages/.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from voicecontrol.events.status import StatusEvent, StatusPublisher, default_status_publisher
from voicecontrol.ui.assets import asset_path
from voicecontrol.ui.pages.background_page import BackgroundControlPage
from voicecontrol.ui.pages.command_history_page import CommandHistoryPage
from voicecontrol.ui.pages.diagnostics_page import DiagnosticsPage
from voicecontrol.ui.pages.logs_page import LogsPage
from voicecontrol.ui.pages.recording_page import RecordingPage
from voicecontrol.ui.pages.settings_page import SettingsPage
from voicecontrol.ui.pages.status_page import StatusPage
from voicecontrol.ui.pages.base import PlaceholderPage


class SettingsWindow(QMainWindow):
    """Apple-style settings window backed by root config.json."""

    def __init__(
        self,
        config: dict[str, Any],
        status_publisher: StatusPublisher | None = None,
        command_history_path: str | Path | None = None,
        log_path: str | Path | None = None,
        diagnostic_path: str | Path | None = None,
        runtime_status_path: str | Path | None = None,
    ) -> None:
        super().__init__()
        self._config = config
        self._status_publisher = status_publisher or default_status_publisher
        self._command_history_path = (
            Path(command_history_path) if command_history_path is not None else None
        )
        self._log_path = Path(log_path) if log_path is not None else None
        self._diagnostic_path = Path(diagnostic_path) if diagnostic_path is not None else None
        self._runtime_status_path = (
            Path(runtime_status_path) if runtime_status_path is not None else None
        )
        self._status_unsubscribe: Callable[[], None] | None = None

        self.setWindowTitle("VoiceControl Settings")
        self.setWindowIcon(QIcon(str(asset_path("app_icon.svg"))))
        self.resize(940, 720)
        self._build_ui()
        self._status_unsubscribe = self._status_publisher.subscribe(self._handle_status_event)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._nav_buttons: list[QPushButton] = []

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 30, 14, 24)
        sidebar_layout.setSpacing(8)

        brand = QLabel("VoiceControl")
        brand.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addSpacing(16)

        self._page_stack = QStackedWidget()
        self._page_stack.setObjectName("pageStack")

        self._status_page = StatusPage(runtime_status_path=self._runtime_status_path)

        nav_pages: list[tuple[str, str, QWidget]] = [
            ("状态", "navStatus", self._status_page),
            ("录音", "navRecording", RecordingPage()),
            ("设置", "navSettings", SettingsPage(self._config)),
            ("TTS", "navTts", PlaceholderPage("TTS", "TTS 控制会显示在这里。", "ttsPage")),
            ("诊断", "navDiagnostics", DiagnosticsPage(self._diagnostic_path)),
            (
                "命令历史",
                "navCommandHistory",
                CommandHistoryPage(self._command_history_path),
            ),
            ("日志查看", "navLogs", LogsPage(self._log_path)),
            (
                "后台控制",
                "navBackgroundControl",
                BackgroundControlPage(
                    config=self._config,
                    log_path=self._log_path,
                    command_history_path=self._command_history_path,
                ),
            ),
        ]

        for index, (label, object_name, page) in enumerate(nav_pages):
            button = QPushButton(label)
            button.setObjectName(object_name)
            button.setProperty("navButton", True)
            button.setCheckable(True)
            button.clicked.connect(
                lambda _checked=False, page_index=index: self._show_page(page_index)
            )
            self._nav_buttons.append(button)
            sidebar_layout.addWidget(button)
            self._page_stack.addWidget(page)

        sidebar_layout.addStretch(1)
        self._show_page(1)

        root_layout.addWidget(sidebar, 0)
        root_layout.addWidget(self._page_stack, 1)
        self.setCentralWidget(root)

    def _show_page(self, index: int) -> None:
        self._page_stack.setCurrentIndex(index)
        for button_index, button in enumerate(self._nav_buttons):
            button.setChecked(button_index == index)

    def _handle_status_event(self, event: StatusEvent) -> None:
        self._status_page.handle_event(event)

    def closeEvent(self, event: Any) -> None:
        if self._status_unsubscribe is not None:
            self._status_unsubscribe()
            self._status_unsubscribe = None
        super().closeEvent(event)

