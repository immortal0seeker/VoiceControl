"""Transparent desktop pet window for runtime status glanceability."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QContextMenuEvent, QMouseEvent
from PySide6.QtWidgets import QLabel, QMenu, QVBoxLayout, QWidget

from voicecontrol.events.status_snapshot import RuntimeStatusSnapshot, read_runtime_status
from voicecontrol.ui.launcher import open_control_center as default_open_control_center


@dataclass(frozen=True)
class PetState:
    """Display state for the floating desktop pet."""

    expression: str
    text: str
    accent_color: str


_STATE_BY_STATUS = {
    "listening": PetState(":)", "监听中", "#34c759"),
    "paused": PetState("--", "已暂停", "#8e8e93"),
    "wake": PetState("HI", "请说", "#30b0c7"),
    "recording": PetState("REC", "录音中", "#ff3b30"),
    "transcribing": PetState("...", "识别中", "#ffcc00"),
    "sending": PetState(">>", "发送中", "#0a84ff"),
    "done": PetState("OK", "已发送", "#34c759"),
    "error": PetState("!", "出错", "#ff453a"),
    "stopped": PetState("ZZ", "已停止", "#8e8e93"),
}

_STANDBY_STATE = PetState("...", "待命", "#8e8e93")


def pet_state_from_snapshot(snapshot: RuntimeStatusSnapshot | None) -> PetState:
    """Convert a runtime status snapshot into compact pet display text."""
    if snapshot is None:
        return _STANDBY_STATE
    return _STATE_BY_STATUS.get(snapshot.current, _STANDBY_STATE)


class DesktopPetWindow(QWidget):
    """Small transparent always-on-top status companion."""

    def __init__(
        self,
        runtime_status_path: str | Path | None = None,
        open_control_center: Callable[[], None] = default_open_control_center,
        poll_interval_ms: int = 1000,
    ) -> None:
        super().__init__()
        self.setObjectName("desktopPetWindow")
        self._runtime_status_path = (
            Path(runtime_status_path) if runtime_status_path is not None else None
        )
        self._open_control_center = open_control_center
        self._drag_start_global: QPoint | None = None
        self._drag_start_window: QPoint | None = None
        self._was_dragged = False

        self.setWindowTitle("VoiceControl Pet")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(128, 96)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self._expression_label = QLabel("...")
        self._expression_label.setObjectName("petExpressionLabel")
        self._expression_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label = QLabel("待命")
        self._status_label.setObjectName("petStatusLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._expression_label, 1)
        layout.addWidget(self._status_label)

        self._timer = QTimer(self)
        self._timer.setObjectName("desktopPetRuntimePollTimer")
        self._timer.setInterval(poll_interval_ms)
        self._timer.timeout.connect(self.refresh_runtime_status)
        self._timer.start()
        self.refresh_runtime_status()

    def refresh_runtime_status(self) -> None:
        """Refresh the pet from the file-backed runtime snapshot."""
        snapshot = read_runtime_status(self._runtime_status_path)
        self._render_state(pet_state_from_snapshot(snapshot))

    def _render_state(self, state: PetState) -> None:
        self._expression_label.setText(state.expression)
        self._status_label.setText(state.text)
        self.setStyleSheet(
            f"""
            QWidget#desktopPetWindow {{
                background: rgba(255, 255, 255, 210);
                border: 2px solid {state.accent_color};
                border-radius: 18px;
            }}
            QLabel#petExpressionLabel {{
                background: transparent;
                color: #1d1d1f;
                font-family: "Segoe UI", "Microsoft YaHei UI", "Arial";
                font-size: 30px;
                font-weight: 800;
            }}
            QLabel#petStatusLabel {{
                background: transparent;
                color: #1d1d1f;
                font-family: "Segoe UI", "Microsoft YaHei UI", "Arial";
                font-size: 14px;
                font-weight: 650;
            }}
            """
        )

    def _build_context_menu(self) -> QMenu:
        menu = QMenu(self)
        open_action = menu.addAction("打开控制中心")
        open_action.triggered.connect(self._handle_pet_clicked)
        quit_action = menu.addAction("退出桌宠")
        quit_action.triggered.connect(self.close)
        return menu

    def _handle_pet_clicked(self) -> None:
        self._open_control_center()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self._build_context_menu().exec(event.globalPos())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_global = event.globalPosition().toPoint()
            self._drag_start_window = self.pos()
            self._was_dragged = False
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start_global is None or self._drag_start_window is None:
            super().mouseMoveEvent(event)
            return
        delta = event.globalPosition().toPoint() - self._drag_start_global
        if delta.manhattanLength() > 4:
            self._was_dragged = True
            self.move(self._drag_start_window + delta)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_start_global is not None:
            if not self._was_dragged:
                self._handle_pet_clicked()
            self._drag_start_global = None
            self._drag_start_window = None
            self._was_dragged = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._timer.stop()
        super().closeEvent(event)
