"""Status page for the VoiceControl settings UI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from voicecontrol.control.commands import (
    PAUSE_LISTENING,
    RESUME_LISTENING,
    START_RECORDING,
    STOP_RECORDING,
    write_control_command,
)
from voicecontrol.events.status import StatusEvent, StatusType
from voicecontrol.events.status_snapshot import RuntimeStatusSnapshot, read_runtime_status
from voicecontrol.ui.widgets import card, switch


def _make_selectable(label: QLabel) -> QLabel:
    label.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse
        | Qt.TextInteractionFlag.TextSelectableByKeyboard
    )
    return label


class StatusPage(QWidget):
    """Displays current pipeline state and the most recent status events."""

    def __init__(
        self,
        runtime_status_path: str | Path | None = None,
        poll_interval_ms: int = 1000,
    ) -> None:
        super().__init__()
        self.setObjectName("recordingPage")

        self._runtime_status_path = Path(runtime_status_path) if runtime_status_path is not None else None
        self._is_recording = False
        self._is_sending = False
        self._last_error = ""
        self._recent_events: list[StatusEvent] = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 30, 36, 28)
        root_layout.setSpacing(0)

        title = QLabel("录音")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        root_layout.addWidget(title)

        subtitle = QLabel("控制监听和录音，并查看最近状态。")
        subtitle.setObjectName("subtitle")
        root_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setObjectName("recordingScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        control_frame, control_layout = card("运行控制")
        listening_row = QHBoxLayout()
        listening_row.setContentsMargins(0, 0, 0, 0)
        listening_row.setSpacing(14)
        listening_label = QLabel("托盘监听")
        listening_label.setObjectName("fieldLabel")
        self._listening_switch = switch(True)
        self._listening_switch.setObjectName("listeningControlSwitch")
        listening_row.addWidget(listening_label, 1)
        listening_row.addWidget(self._listening_switch, 0)
        control_layout.addLayout(listening_row)

        recording_controls = QHBoxLayout()
        recording_controls.setContentsMargins(0, 0, 0, 0)
        recording_controls.setSpacing(14)
        start_button = QPushButton("开始录音")
        start_button.setObjectName("statusStartRecordingButton")
        stop_button = QPushButton("停止录音")
        stop_button.setObjectName("statusStopRecordingButton")
        recording_controls.addWidget(start_button)
        recording_controls.addWidget(stop_button)
        recording_controls.addStretch(1)
        control_layout.addLayout(recording_controls)

        self._control_result_label = _make_selectable(QLabel(""))
        self._control_result_label.setObjectName("statusControlResultLabel")
        self._control_result_label.setWordWrap(True)
        control_layout.addWidget(self._control_result_label)
        content_layout.addWidget(control_frame)

        frame, layout = card("当前状态")
        self._current_status_label = _make_selectable(QLabel("当前状态：未收到事件"))
        self._current_status_label.setObjectName("currentStatusLabel")
        self._is_recording_label = _make_selectable(QLabel("录音中：否"))
        self._is_recording_label.setObjectName("isRecordingLabel")
        self._is_sending_label = _make_selectable(QLabel("发送中：否"))
        self._is_sending_label.setObjectName("isSendingLabel")
        self._last_error_label = _make_selectable(QLabel("最近错误：无"))
        self._last_error_label.setObjectName("lastErrorLabel")
        self._runtime_status_updated_at_label = _make_selectable(QLabel("最后更新时间：未知"))
        self._runtime_status_updated_at_label.setObjectName("runtimeStatusUpdatedAtLabel")
        self._runtime_status_hint_label = _make_selectable(QLabel(""))
        self._runtime_status_hint_label.setObjectName("runtimeStatusHintLabel")
        self._runtime_status_hint_label.setWordWrap(True)
        self._recent_status_events_label = _make_selectable(QLabel("暂无状态事件。"))
        self._recent_status_events_label.setObjectName("recentStatusEventsLabel")
        self._recent_status_events_label.setWordWrap(True)

        layout.addWidget(self._current_status_label)
        layout.addWidget(self._is_recording_label)
        layout.addWidget(self._is_sending_label)
        layout.addWidget(self._last_error_label)
        layout.addWidget(self._runtime_status_updated_at_label)
        layout.addWidget(self._runtime_status_hint_label)
        layout.addWidget(self._recent_status_events_label)
        content_layout.addWidget(frame)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

        self._listening_switch.toggled.connect(self._toggle_listening)
        start_button.clicked.connect(
            lambda: self._send_control_command(START_RECORDING, "已请求开始录音。")
        )
        stop_button.clicked.connect(
            lambda: self._send_control_command(STOP_RECORDING, "已请求停止录音。")
        )

        self._runtime_status_timer = QTimer(self)
        self._runtime_status_timer.setObjectName("runtimeStatusPollTimer")
        self._runtime_status_timer.setInterval(poll_interval_ms)
        self._runtime_status_timer.timeout.connect(self.refresh_runtime_status)
        self._runtime_status_timer.start()
        self.refresh_runtime_status()

    def _toggle_listening(self, enabled: bool) -> None:
        if enabled:
            self._send_control_command(RESUME_LISTENING, "已请求恢复监听。")
        else:
            self._send_control_command(PAUSE_LISTENING, "已请求暂停监听。")

    def _send_control_command(self, command: str, success_message: str) -> None:
        try:
            write_control_command(command)
        except Exception as exc:
            self._control_result_label.setText(f"失败：{exc}")
            return
        self._control_result_label.setText(success_message)

    def handle_event(self, event: StatusEvent) -> None:
        """Update the page in response to an in-process status event."""
        self._recent_events.append(event)
        self._recent_events = self._recent_events[-8:]
        self._is_recording = event.type == StatusType.RECORDING
        self._is_sending = event.type == StatusType.SENDING
        if event.type == StatusType.ERROR:
            self._last_error = event.message or "未知错误"

        recent_events = [
            {
                "type": item.type.value,
                "message": item.message,
                "created_at": item.created_at.strftime("%H:%M:%S"),
            }
            for item in self._recent_events
        ]
        self._render_snapshot(
            RuntimeStatusSnapshot(
                current=event.type.value,
                message=event.message,
                is_recording=self._is_recording,
                is_sending=self._is_sending,
                last_error=self._last_error or None,
                recent_events=recent_events,
            )
        )

    def refresh_runtime_status(self) -> None:
        """Refresh labels from the cross-process runtime status snapshot."""
        snapshot = read_runtime_status(self._runtime_status_path)
        if snapshot is not None:
            self._render_snapshot(snapshot)
        else:
            self._runtime_status_hint_label.setText("托盘未运行或状态文件不存在。")
            self._runtime_status_updated_at_label.setText("最后更新时间：未知")

    def _render_snapshot(self, snapshot: RuntimeStatusSnapshot) -> None:
        self._current_status_label.setText(f"当前状态：{snapshot.current or '未收到事件'}")
        self._is_recording_label.setText(f"录音中：{'是' if snapshot.is_recording else '否'}")
        self._is_sending_label.setText(f"发送中：{'是' if snapshot.is_sending else '否'}")
        self._last_error_label.setText(f"最近错误：{snapshot.last_error or '无'}")
        self._runtime_status_updated_at_label.setText(
            f"最后更新时间：{snapshot.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self._runtime_status_hint_label.setText("")

        lines = []
        for event in snapshot.recent_events:
            event_type = str(event.get("type") or "")
            message = str(event.get("message") or "")
            created_at = str(event.get("created_at") or "")
            suffix = f" - {message}" if message else ""
            lines.append(f"{created_at} {event_type}{suffix}".strip())
        self._recent_status_events_label.setText("\n".join(lines) if lines else "暂无状态事件。")
