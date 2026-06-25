"""System-tray daemon for VoiceControl.

Runs the always-on wake-word loop in a background thread and exposes a tray
icon to pause/resume listening, toggle launch-at-logon, and quit. Launched via
``pythonw.exe -m voicecontrol.tray_app`` it runs headless in the user session
(so it can still drive the Codex desktop window — unlike a session-0 Windows
Service).
"""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from voicecontrol.config import settings
from voicecontrol.control.commands import START_RECORDING, STOP_RECORDING, read_control_command
from voicecontrol.utils import autostart

if TYPE_CHECKING:
    from voicecontrol.pipeline.orchestrator import PipelineResult

logger = logging.getLogger(__name__)

_STAGE_TITLES = {
    "loading": "加载中…",
    "listening": f"监听中（说 {settings.WAKE_WORD_MODEL}）",
    "wake": "已唤醒，请说话…",
    "transcribing": "识别中…",
    "done": "已发送到 Codex",
}


def _configure_logging() -> None:
    # Background (tray) mode: logs go to a daily file under LOG_DIR (no console with pythonw).
    # Foreground CLI (main.py) logs to the console instead; see main.main().
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(settings.log_file_path(), encoding="utf-8")],
    )


def _make_icon_image() -> Image.Image:
    """A simple round 'V' badge for the tray."""
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, size - 4, size - 4), fill=(40, 120, 220, 255))
    draw.line((20, 22, 32, 44), fill="white", width=5)
    draw.line((44, 22, 32, 44), fill="white", width=5)
    return image


def _load_tray_icon_image() -> Image.Image:
    """Load the shared app icon asset, falling back to a generated badge."""
    try:
        from voicecontrol.ui.assets import asset_path

        with Image.open(asset_path("app_icon.png")) as image:
            return image.convert("RGBA").copy()
    except OSError:
        logger.exception("Failed to load tray icon asset; using fallback icon.")
        return _make_icon_image()


def open_settings_window() -> None:
    """Open the settings UI in a separate Python process."""
    subprocess.Popen(
        [sys.executable, "-m", "voicecontrol.ui.settings_app"],
        close_fds=True,
    )


class TrayApp:
    """Owns the tray icon, the worker thread, and shared control flags."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._paused = threading.Event()
        self._manual_record_event = threading.Event()
        self._recording_stop_event = threading.Event()
        self._is_recording = False
        self._icon = Icon(
            "VoiceControl",
            icon=_load_tray_icon_image(),
            title="VoiceControl — 加载中…",
            menu=Menu(
                MenuItem(self._pause_label, self._on_toggle_pause),
                MenuItem(self._recording_label, self._on_toggle_recording),
                MenuItem("打开设置", self._on_open_settings),
                MenuItem(
                    "开机自启",
                    self._on_toggle_autostart,
                    checked=lambda _item: autostart.is_enabled(),
                ),
                Menu.SEPARATOR,
                MenuItem("退出", self._on_quit),
            ),
        )

    # --- menu handlers -----------------------------------------------------
    def _pause_label(self, _item: object) -> str:
        return "恢复监听" if self._paused.is_set() else "暂停监听"

    def _recording_label(self, _item: object) -> str:
        return "停止录音" if self._is_recording else "开始录音"

    def _on_toggle_pause(self, _icon: Icon, _item: object) -> None:
        if self._paused.is_set():
            self._paused.clear()
            self._set_stage("listening")
        else:
            self._paused.set()
            self._icon.title = "VoiceControl — 已暂停"
        self._icon.update_menu()

    def _on_toggle_recording(self, _icon: Icon, _item: object) -> None:
        if self._is_recording:
            logger.info("Manual recording stop requested from tray.")
            self._handle_control_command(STOP_RECORDING)
        else:
            logger.info("Manual recording requested from tray.")
            self._handle_control_command(START_RECORDING)
        self._icon.update_menu()

    def _handle_control_command(self, command: str) -> None:
        if command == START_RECORDING:
            self._manual_record_event.set()
            self._is_recording = True
        elif command == STOP_RECORDING:
            self._recording_stop_event.set()
            self._is_recording = False

    def _on_open_settings(self, _icon: Icon, _item: object) -> None:
        try:
            open_settings_window()
        except OSError:
            logger.exception("Failed to open settings UI.")

    def _on_toggle_autostart(self, _icon: Icon, _item: object) -> None:
        enabled = autostart.toggle()
        logger.info("Autostart toggled -> %s", enabled)
        self._icon.update_menu()

    def _on_quit(self, _icon: Icon, _item: object) -> None:
        logger.info("Quit requested from tray.")
        self._stop_event.set()
        self._icon.stop()

    # --- worker ------------------------------------------------------------
    def _set_stage(self, stage: str, _result: PipelineResult | None = None) -> None:
        if stage == "wake":
            self._is_recording = True
        elif stage in {"transcribing", "done", "listening", "paused", "stopped", "error"}:
            self._is_recording = False
        self._icon.update_menu()
        self._icon.title = f"VoiceControl — {_STAGE_TITLES.get(stage, stage)}"

    def _worker(self) -> None:
        try:
            from voicecontrol.pipeline.orchestrator import VoiceOrchestrator
            from voicecontrol.wake_word.detector import WakeWordDetector

            orchestrator = VoiceOrchestrator()
            orchestrator.load()
            detector = WakeWordDetector()
            self._set_stage("listening")
            orchestrator.run_wake_loop(
                detector=detector,
                stop_event=self._stop_event,
                is_active=lambda: not self._paused.is_set(),
                on_event=self._set_stage,
                manual_stop_key=settings.RECORD_HOTKEY,
                manual_record_event=self._manual_record_event,
                recording_stop_event=self._recording_stop_event,
            )
        except Exception:
            logger.exception("Wake loop crashed.")
            self._icon.title = "VoiceControl — 出错（见日志）"

    def _control_worker(self) -> None:
        while not self._stop_event.is_set():
            command = read_control_command()
            if command == START_RECORDING:
                logger.info("Manual recording requested from control command.")
                self._handle_control_command(command)
                self._icon.update_menu()
            elif command == STOP_RECORDING:
                logger.info("Manual recording stop requested from control command.")
                self._handle_control_command(command)
                self._icon.update_menu()
            self._stop_event.wait(timeout=0.25)

    def _setup(self, icon: Icon) -> None:
        icon.visible = True
        threading.Thread(target=self._worker, name="wake-loop", daemon=True).start()
        threading.Thread(target=self._control_worker, name="control-loop", daemon=True).start()

    def run(self) -> None:
        self._icon.run(self._setup)


def main() -> int:
    _configure_logging()
    logger.info("Tray app starting.")
    TrayApp().run()
    logger.info("Tray app stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
