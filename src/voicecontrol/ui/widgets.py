"""Reusable PySide6 widgets for the settings UI."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, Property
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class Switch(QCheckBox):
    """A compact iOS-style switch for boolean settings."""

    def __init__(self, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(56, 32)
        self._offset = 1.0 if checked else 0.0
        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._start_animation)

    def sizeHint(self) -> QSize:
        return QSize(56, 32)

    def hitButton(self, pos) -> bool:  # noqa: ANN001
        return self.rect().contains(pos)

    def _start_animation(self, checked: bool) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._offset)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    offset = Property(float, _get_offset, _set_offset)

    def paintEvent(self, event) -> None:  # noqa: ANN001
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track = QRectF(1, 3, 54, 26)
        track_color = QColor("#34c759") if self.isChecked() else QColor("#d2d2d7")
        if not self.isEnabled():
            track_color = QColor("#e5e5ea")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track, 13, 13)

        knob_size = 22
        left = 3 + self._offset * 26
        knob = QRectF(left, 5, knob_size, knob_size)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(knob)

        painter.setPen(QColor(0, 0, 0, 28))
        painter.drawEllipse(knob.adjusted(0.5, 0.5, -0.5, -0.5))


def make_label(title: str, hint: str | None = None) -> QWidget:
    box = QWidget()
    box.setStyleSheet("background: transparent;")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)

    label = QLabel(title)
    label.setObjectName("fieldLabel")
    layout.addWidget(label)

    if hint:
        hint_label = QLabel(hint)
        hint_label.setObjectName("fieldHint")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

    return box


def add_row(layout: QVBoxLayout, label: str, editor: QWidget, hint: str | None = None) -> None:
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(20)
    row.addWidget(make_label(label, hint), 1)
    row.addWidget(editor, 0)
    layout.addLayout(row)


def combo(current: str | None, options: list[str]) -> QComboBox:
    widget = QComboBox()
    widget.addItems(options)
    if current in options:
        widget.setCurrentText(current)
    widget.setMinimumWidth(180)
    return widget


def double_spin(value: float, minimum: float, maximum: float, step: float) -> QDoubleSpinBox:
    widget = QDoubleSpinBox()
    widget.setRange(minimum, maximum)
    widget.setSingleStep(step)
    widget.setDecimals(2)
    widget.setValue(float(value))
    widget.setMinimumWidth(140)
    return widget


def int_spin(value: int, minimum: int, maximum: int, step: int = 1) -> QSpinBox:
    widget = QSpinBox()
    widget.setRange(minimum, maximum)
    widget.setSingleStep(step)
    widget.setValue(int(value))
    widget.setMinimumWidth(140)
    return widget


def line_edit(value: str | None, placeholder: str = "") -> QLineEdit:
    widget = QLineEdit("" if value is None else str(value))
    widget.setPlaceholderText(placeholder)
    widget.setMinimumWidth(220)
    return widget


def switch(checked: bool) -> Switch:
    return Switch(checked=checked)


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    frame_layout = QVBoxLayout(frame)
    frame_layout.setContentsMargins(22, 18, 22, 20)
    frame_layout.setSpacing(16)

    heading = QLabel(title)
    heading.setObjectName("sectionTitle")
    frame_layout.addWidget(heading)
    return frame, frame_layout
