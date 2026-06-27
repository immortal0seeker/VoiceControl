"""Stylesheets for the VoiceControl PySide6 UI."""

from __future__ import annotations

from voicecontrol.ui.assets import asset_path


def _qss_url(name: str) -> str:
    """Return a Qt stylesheet URL path for a bundled asset."""
    return asset_path(name).as_posix()


def apple_style_sheet() -> str:
    """Return a soft Apple-inspired Qt stylesheet."""
    chevron_down = _qss_url("chevron_down.svg")
    chevron_up = _qss_url("chevron_up.svg")
    template = """
    QWidget {
        background: #f5f5f7;
        color: #1d1d1f;
        font-family: "Segoe UI", "Microsoft YaHei UI", "Arial";
        font-size: 14px;
    }
    QLabel#title {
        font-size: 30px;
        font-weight: 700;
        color: #1d1d1f;
        padding-bottom: 4px;
    }
    QLabel#subtitle {
        color: #6e6e73;
        font-size: 13px;
        padding-bottom: 18px;
    }
    QWidget#sidebar {
        background: #ededf0;
        border-right: 1px solid #d9d9de;
    }
    QLabel#sidebarTitle {
        color: #1d1d1f;
        font-size: 18px;
        font-weight: 700;
        background: transparent;
    }
    QPushButton[navButton="true"] {
        background: transparent;
        color: #1d1d1f;
        border: none;
        border-radius: 8px;
        padding: 10px 12px;
        text-align: left;
        font-weight: 600;
    }
    QPushButton[navButton="true"]:hover {
        background: #e1e1e6;
    }
    QPushButton[navButton="true"]:checked {
        background: #d8e9ff;
        color: #0057c2;
    }
    QLabel#sectionTitle {
        color: #1d1d1f;
        font-size: 17px;
        font-weight: 650;
        background: transparent;
    }
    QLabel#fieldLabel {
        color: #1d1d1f;
        background: transparent;
    }
    QLabel#fieldHint {
        color: #86868b;
        font-size: 12px;
        background: transparent;
    }
    QFrame#card {
        background: #ffffff;
        border: 1px solid #e6e6eb;
        border-radius: 18px;
    }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background: #f5f5f7;
        border: 1px solid #d2d2d7;
        border-radius: 10px;
        padding: 7px 10px;
        min-height: 22px;
    }
    QComboBox, QSpinBox, QDoubleSpinBox {
        padding-right: 34px;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border: 1px solid #007aff;
        background: #ffffff;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 34px;
        border: none;
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
        background: transparent;
    }
    QComboBox::down-arrow {
        image: url("__CHEVRON_DOWN__");
        width: 14px;
        height: 14px;
    }
    QComboBox::down-arrow:on {
        top: 1px;
    }
    QAbstractSpinBox::up-button,
    QAbstractSpinBox::down-button {
        subcontrol-origin: border;
        width: 28px;
        border: none;
        background: transparent;
    }
    QAbstractSpinBox::up-button {
        subcontrol-position: top right;
        border-top-right-radius: 10px;
    }
    QAbstractSpinBox::down-button {
        subcontrol-position: bottom right;
        border-bottom-right-radius: 10px;
    }
    QAbstractSpinBox::up-button:hover,
    QAbstractSpinBox::down-button:hover {
        background: #e9e9ef;
    }
    QAbstractSpinBox::up-arrow {
        image: url("__CHEVRON_UP__");
        width: 12px;
        height: 12px;
    }
    QAbstractSpinBox::down-arrow {
        image: url("__CHEVRON_DOWN__");
        width: 12px;
        height: 12px;
    }
    QPushButton {
        background: #007aff;
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 9px 18px;
        font-weight: 600;
    }
    QPushButton:hover {
        background: #0a84ff;
    }
    QPushButton:pressed {
        background: #0066d6;
    }
    QPushButton#secondary {
        background: #e9e9ef;
        color: #1d1d1f;
    }
    QPushButton#secondary:hover {
        background: #dedee6;
    }
    QScrollArea {
        border: none;
    }
    QScrollBar:vertical {
        background: transparent;
        width: 10px;
        margin: 4px 0 4px 0;
        border: none;
    }
    QScrollBar::handle:vertical {
        background: #c7c7cc;
        border-radius: 5px;
        min-height: 42px;
    }
    QScrollBar::handle:vertical:hover {
        background: #aeaeb2;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
        border: none;
        background: transparent;
    }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 10px;
        margin: 0 4px 0 4px;
        border: none;
    }
    QScrollBar::handle:horizontal {
        background: #c7c7cc;
        border-radius: 5px;
        min-width: 42px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #aeaeb2;
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0;
        border: none;
        background: transparent;
    }
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: transparent;
    }
    """
    return (
        template
        .replace("__CHEVRON_DOWN__", chevron_down)
        .replace("__CHEVRON_UP__", chevron_up)
    )
