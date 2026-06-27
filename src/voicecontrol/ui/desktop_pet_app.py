"""Entry point for the VoiceControl desktop pet."""

from __future__ import annotations

import sys

from voicecontrol.ui.desktop_pet import DesktopPetWindow


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("PySide6 is not installed. Install it with:")
        print(r".venv\Scripts\pip.exe install PySide6")
        return 1

    app = QApplication(sys.argv)
    window = DesktopPetWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
