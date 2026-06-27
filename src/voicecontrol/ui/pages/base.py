"""Shared page scaffolding for the settings UI."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


def page_layout(page: QWidget, title_text: str, subtitle_text: str) -> QVBoxLayout:
    """Add a standard title + subtitle to *page* and return its root layout."""
    root_layout = QVBoxLayout(page)
    root_layout.setContentsMargins(36, 30, 36, 28)
    root_layout.setSpacing(0)

    title = QLabel(title_text)
    title.setObjectName("title")
    title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
    root_layout.addWidget(title)

    subtitle = QLabel(subtitle_text)
    subtitle.setObjectName("subtitle")
    root_layout.addWidget(subtitle)
    return root_layout


class PlaceholderPage(QWidget):
    """Empty placeholder page used for not-yet-implemented sections."""

    def __init__(self, title_text: str, empty_text: str, object_name: str = "") -> None:
        super().__init__()
        if object_name:
            self.setObjectName(object_name)
        layout = page_layout(self, title_text, empty_text)
        layout.addStretch(1)
