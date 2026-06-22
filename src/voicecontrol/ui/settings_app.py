"""Entry point for the VoiceControl settings UI.

Run with:
    python -m voicecontrol.ui.settings_app
"""

from __future__ import annotations

import sys

from voicecontrol.config.manager import ConfigError, load_config
from voicecontrol.ui.style import apple_style_sheet
from voicecontrol.ui.settings_window import SettingsWindow


PYSIDE6_INSTALL_HINT = (
    "PySide6 is not installed. Install it with:\n"
    r".venv\Scripts\pip.exe install PySide6"
)


def main() -> int:
    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication

        config = load_config()
    except ImportError:
        print(PYSIDE6_INSTALL_HINT)
        return 1
    except ConfigError as exc:
        print(exc)
        return 1

    app = QApplication(sys.argv)
    app.setStyleSheet(apple_style_sheet())
    from voicecontrol.ui.assets import asset_path

    app.setWindowIcon(QIcon(str(asset_path("app_icon.svg"))))

    window = SettingsWindow(config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
