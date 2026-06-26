"""Settings window layout and config binding logic."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from voicecontrol.control.commands import START_RECORDING, STOP_RECORDING, write_control_command
from voicecontrol.config.manager import ConfigError, load_config, save_config
from voicecontrol.tts.speaker import TextSpeaker, TtsError
from voicecontrol.ui.assets import asset_path
from voicecontrol.ui.widgets import add_row, card, combo, double_spin, int_spin, line_edit, switch
from voicecontrol.wake_word.models import available_wake_word_models

Binding = tuple[tuple[str, ...], Callable[[], Any]]


def _get_nested(config: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = config
    for key in path:
        value = value[key]
    return value


def _set_nested(config: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    target = config
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def _optional_float_text(text: str) -> float | None:
    stripped = text.strip()
    return None if stripped == "" else float(stripped)


def _register(bindings: list[Binding], path: tuple[str, ...], reader: Callable[[], Any]) -> None:
    bindings.append((path, reader))


class SettingsWindow(QMainWindow):
    """Apple-style settings window backed by root config.json."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self._config = config
        self._bindings: list[Binding] = []
        self.setWindowTitle("VoiceControl Settings")
        self.setWindowIcon(QIcon(str(asset_path("app_icon.svg"))))
        self.resize(940, 720)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._recording_nav = QPushButton("Recording")
        self._recording_nav.setObjectName("navRecording")
        self._settings_nav = QPushButton("Settings")
        self._settings_nav.setObjectName("navSettings")
        for button in (self._recording_nav, self._settings_nav):
            button.setCheckable(True)

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
        sidebar_layout.addWidget(self._recording_nav)
        sidebar_layout.addWidget(self._settings_nav)
        sidebar_layout.addStretch(1)

        self._page_stack = QStackedWidget()
        self._page_stack.setObjectName("pageStack")
        self._recording_page = self._build_recording_page()
        self._settings_page = self._build_settings_page()
        self._page_stack.addWidget(self._recording_page)
        self._page_stack.addWidget(self._settings_page)

        self._recording_nav.clicked.connect(lambda: self._show_page(0))
        self._settings_nav.clicked.connect(lambda: self._show_page(1))
        self._show_page(0)

        root_layout.addWidget(sidebar, 0)
        root_layout.addWidget(self._page_stack, 1)
        self.setCentralWidget(root)

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsPage")
        root_layout = QVBoxLayout(page)
        root_layout.setContentsMargins(36, 30, 36, 28)
        root_layout.setSpacing(0)

        title = QLabel("Settings")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        root_layout.addWidget(title)

        subtitle = QLabel("设置语音助手的录音、识别、唤醒和桌面发送行为。")
        subtitle.setObjectName("subtitle")
        root_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        self._add_audio_card(content_layout)
        self._add_stt_card(content_layout)
        self._add_vad_card(content_layout)
        self._add_wake_card(content_layout)
        self._add_executor_card(content_layout)
        self._add_tts_card(content_layout)
        self._add_feedback_card(content_layout)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)
        root_layout.addLayout(self._footer())
        return page

    def _build_recording_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("recordingPage")
        root_layout = QVBoxLayout(page)
        root_layout.setContentsMargins(36, 30, 36, 28)
        root_layout.setSpacing(0)

        title = QLabel("Recording")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        root_layout.addWidget(title)

        subtitle = QLabel("控制托盘后台的录音流程。")
        subtitle.setObjectName("subtitle")
        root_layout.addWidget(subtitle)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)
        self._add_recording_control_card(content_layout)
        content_layout.addStretch(1)
        root_layout.addWidget(content, 1)
        return page

    def _show_page(self, index: int) -> None:
        self._page_stack.setCurrentIndex(index)
        self._recording_nav.setChecked(index == 0)
        self._settings_nav.setChecked(index == 1)

    def _footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 18, 0, 0)
        footer.setSpacing(14)
        footer.addStretch(1)

        reset_button = QPushButton("重新载入")
        reset_button.setObjectName("secondary")
        save_button = QPushButton("保存设置")
        save_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        footer.addWidget(reset_button)
        footer.addWidget(save_button)

        save_button.clicked.connect(self._save_current)
        reset_button.clicked.connect(self._reload_window)
        return footer

    def _add_recording_control_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Recording")
        start_button = QPushButton("开始录音")
        stop_button = QPushButton("停止录音")
        stop_button.setObjectName("secondary")

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(14)
        controls.addWidget(start_button)
        controls.addWidget(stop_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        start_button.clicked.connect(self._request_start_recording)
        stop_button.clicked.connect(self._request_stop_recording)
        content_layout.addWidget(frame)

    def _request_start_recording(self) -> None:
        write_control_command(START_RECORDING)
        QMessageBox.information(self, "已发送", "已请求托盘后台开始录音。")

    def _request_stop_recording(self) -> None:
        write_control_command(STOP_RECORDING)
        QMessageBox.information(self, "已发送", "已请求托盘后台停止录音。")

    def _add_audio_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Audio")
        input_device = line_edit(_get_nested(self._config, ("audio", "input_device")), "留空使用系统默认麦克风")
        add_row(layout, "麦克风设备", input_device, "填 sounddevice 设备编号；留空表示默认输入设备。")
        _register(
            self._bindings,
            ("audio", "input_device"),
            lambda: None if input_device.text().strip() == "" else int(input_device.text()),
        )
        content_layout.addWidget(frame)

    def _add_stt_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Speech Recognition")
        whisper_model = combo(_get_nested(self._config, ("stt", "whisper_model_size")), ["small", "medium", "large-v3"])
        whisper_device = combo(_get_nested(self._config, ("stt", "whisper_device")), ["cuda", "cpu"])
        whisper_compute = combo(_get_nested(self._config, ("stt", "whisper_compute_type")), ["float16", "int8", "float32"])
        whisper_beam = int_spin(_get_nested(self._config, ("stt", "whisper_beam_size")), 1, 10)
        whisper_vad = switch(_get_nested(self._config, ("stt", "whisper_vad_filter")))

        add_row(layout, "Whisper 模型", whisper_model, "small 更快，medium/large-v3 更准但更吃显存。")
        add_row(layout, "计算设备", whisper_device, "有 NVIDIA CUDA 时用 cuda；否则用 cpu。")
        add_row(layout, "计算精度", whisper_compute, "GPU 常用 float16，CPU 常用 int8。")
        add_row(layout, "Beam Size", whisper_beam, "越大可能更准，但速度更慢。")
        add_row(layout, "Whisper VAD 过滤", whisper_vad, "过滤静音和噪声，减少幻觉文本。")

        _register(self._bindings, ("stt", "whisper_model_size"), whisper_model.currentText)
        _register(self._bindings, ("stt", "whisper_device"), whisper_device.currentText)
        _register(self._bindings, ("stt", "whisper_compute_type"), whisper_compute.currentText)
        _register(self._bindings, ("stt", "whisper_beam_size"), whisper_beam.value)
        _register(self._bindings, ("stt", "whisper_vad_filter"), whisper_vad.isChecked)
        content_layout.addWidget(frame)

    def _add_vad_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Auto Stop")
        speech_threshold = double_spin(_get_nested(self._config, ("vad", "speech_threshold")), 0.05, 0.95, 0.05)
        silence_duration = double_spin(_get_nested(self._config, ("vad", "silence_duration")), 0.5, 10.0, 0.25)
        max_record = line_edit(_get_nested(self._config, ("vad", "max_record_seconds")), "180")
        start_timeout = double_spin(_get_nested(self._config, ("vad", "start_timeout")), 1.0, 60.0, 1.0)

        add_row(layout, "语音阈值", speech_threshold, "越低越敏感，也越容易把噪声当成人声。")
        add_row(layout, "静音停录秒数", silence_duration, "说完后静音多久自动停止录音。")
        add_row(layout, "最长录音秒数", max_record, "留空取消硬上限；请使用托盘、F9 或手动停止。")
        add_row(layout, "起始超时秒数", start_timeout, "开始录音后多久没说话就放弃。")

        _register(self._bindings, ("vad", "speech_threshold"), speech_threshold.value)
        _register(self._bindings, ("vad", "silence_duration"), silence_duration.value)
        _register(self._bindings, ("vad", "max_record_seconds"), lambda: _optional_float_text(max_record.text()))
        _register(self._bindings, ("vad", "start_timeout"), start_timeout.value)
        content_layout.addWidget(frame)

    def _add_wake_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Wake Word")
        wake_model = combo(_get_nested(self._config, ("wake_word", "model")), available_wake_word_models())
        wake_threshold = double_spin(_get_nested(self._config, ("wake_word", "threshold")), 0.05, 0.95, 0.05)
        wake_cooldown = double_spin(_get_nested(self._config, ("wake_word", "cooldown")), 0.0, 10.0, 0.5)

        add_row(layout, "唤醒词模型", wake_model, "当前使用 openWakeWord 预训练模型。")
        add_row(layout, "唤醒阈值", wake_threshold, "越低越容易唤醒，也更容易误触发。")
        add_row(layout, "冷却秒数", wake_cooldown, "上一条命令结束后，短时间内忽略重复唤醒。")

        _register(self._bindings, ("wake_word", "model"), wake_model.currentText)
        _register(self._bindings, ("wake_word", "threshold"), wake_threshold.value)
        _register(self._bindings, ("wake_word", "cooldown"), wake_cooldown.value)
        content_layout.addWidget(frame)

    def _add_executor_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Codex")
        codex_title = line_edit(_get_nested(self._config, ("executor", "codex_window_title")), "Codex")
        codex_launch = line_edit(_get_nested(self._config, ("executor", "codex_launch_command")), r"C:\Path\To\Codex.exe")
        codex_launch.setObjectName("codexLaunchCommand")
        auto_enter = switch(_get_nested(self._config, ("executor", "send_prompt_auto_enter")))
        click_before_paste = switch(_get_nested(self._config, ("executor", "click_composer_before_paste")))
        click_x = double_spin(_get_nested(self._config, ("executor", "composer_click_rel_x")), 0.0, 1.0, 0.05)
        click_y = double_spin(_get_nested(self._config, ("executor", "composer_click_rel_y")), 0.0, 1.0, 0.05)

        add_row(layout, "窗口标题", codex_title, "用于查找 Codex Desktop 窗口的标题子串。")
        add_row(layout, "启动命令", codex_launch, "找不到窗口时尝试启动；留空则只报错。")
        add_row(layout, "粘贴后自动回车", auto_enter)
        add_row(layout, "粘贴前点击输入框", click_before_paste)
        add_row(layout, "输入框 X 位置", click_x, "窗口内相对坐标，0 左侧，1 右侧。")
        add_row(layout, "输入框 Y 位置", click_y, "窗口内相对坐标，0 顶部，1 底部。")

        _register(self._bindings, ("executor", "codex_window_title"), lambda: codex_title.text().strip())
        _register(self._bindings, ("executor", "codex_launch_command"), lambda: codex_launch.text().strip())
        _register(self._bindings, ("executor", "send_prompt_auto_enter"), auto_enter.isChecked)
        _register(self._bindings, ("executor", "click_composer_before_paste"), click_before_paste.isChecked)
        _register(self._bindings, ("executor", "composer_click_rel_x"), click_x.value)
        _register(self._bindings, ("executor", "composer_click_rel_y"), click_y.value)
        content_layout.addWidget(frame)

    def _add_tts_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Text to Speech")
        tts_enabled = switch(_get_nested(self._config, ("tts", "enabled")))
        tts_enabled.setObjectName("ttsEnabled")
        tts_rate = int_spin(_get_nested(self._config, ("tts", "rate")), -10, 10, 1)
        tts_rate.setObjectName("ttsRate")
        tts_volume = int_spin(_get_nested(self._config, ("tts", "volume")), 0, 100, 5)
        tts_volume.setObjectName("ttsVolume")
        tts_voice = line_edit(_get_nested(self._config, ("tts", "voice")), "留空使用系统默认语音")
        tts_voice.setObjectName("ttsVoice")
        test_button = QPushButton("测试 TTS")
        test_button.setObjectName("testTtsButton")

        add_row(layout, "启用语音播报", tts_enabled)
        add_row(layout, "语速", tts_rate, "Windows SAPI 语速，-10 到 10。")
        add_row(layout, "音量", tts_volume, "0 到 100。")
        add_row(layout, "语音名称", tts_voice, "可填写系统语音名称的一部分；留空使用默认语音。")
        layout.addWidget(test_button, 0, Qt.AlignmentFlag.AlignRight)

        _register(self._bindings, ("tts", "enabled"), tts_enabled.isChecked)
        _register(self._bindings, ("tts", "rate"), tts_rate.value)
        _register(self._bindings, ("tts", "volume"), tts_volume.value)
        _register(
            self._bindings,
            ("tts", "voice"),
            lambda: None if tts_voice.text().strip() == "" else tts_voice.text().strip(),
        )
        test_button.clicked.connect(
            lambda: self._test_tts(
                enabled=tts_enabled.isChecked(),
                rate=tts_rate.value(),
                volume=tts_volume.value(),
                voice=None if tts_voice.text().strip() == "" else tts_voice.text().strip(),
            )
        )
        content_layout.addWidget(frame)

    def _test_tts(self, enabled: bool, rate: int, volume: int, voice: str | None) -> None:
        if not enabled:
            QMessageBox.information(self, "TTS 已关闭", "请先启用语音播报。")
            return
        try:
            TextSpeaker(enabled=True, rate=rate, volume=volume, voice=voice).speak("我在")
        except TtsError as exc:
            QMessageBox.warning(self, "TTS 测试失败", str(exc))

    def _add_feedback_card(self, content_layout: QVBoxLayout) -> None:
        frame, layout = card("Feedback")
        feedback_enabled = switch(_get_nested(self._config, ("feedback", "enabled")))
        wake_freq = int_spin(_get_nested(self._config, ("feedback", "wake_freq")), 100, 3000, 10)
        wake_ms = int_spin(_get_nested(self._config, ("feedback", "wake_ms")), 20, 1000, 10)
        done_freq = int_spin(_get_nested(self._config, ("feedback", "done_freq")), 100, 3000, 10)
        done_ms = int_spin(_get_nested(self._config, ("feedback", "done_ms")), 20, 1000, 10)

        add_row(layout, "启用提示音", feedback_enabled)
        add_row(layout, "唤醒提示频率", wake_freq)
        add_row(layout, "唤醒提示时长", wake_ms)
        add_row(layout, "完成提示频率", done_freq)
        add_row(layout, "完成提示时长", done_ms)

        _register(self._bindings, ("feedback", "enabled"), feedback_enabled.isChecked)
        _register(self._bindings, ("feedback", "wake_freq"), wake_freq.value)
        _register(self._bindings, ("feedback", "wake_ms"), wake_ms.value)
        _register(self._bindings, ("feedback", "done_freq"), done_freq.value)
        _register(self._bindings, ("feedback", "done_ms"), done_ms.value)
        content_layout.addWidget(frame)

    def _save_current(self) -> None:
        next_config = load_config()
        try:
            for path, reader in self._bindings:
                _set_nested(next_config, path, reader())
            save_config(next_config)
        except ValueError as exc:
            QMessageBox.warning(self, "保存失败", f"请检查输入格式：{exc}")
            return
        except ConfigError as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
            return
        QMessageBox.information(self, "已保存", "配置已写入 config.json。重启监听进程后生效。")

    def _reload_window(self) -> None:
        try:
            fresh = load_config()
        except ConfigError as exc:
            QMessageBox.critical(self, "读取失败", str(exc))
            return
        self._config = fresh
        self._bindings = []
        self._build_ui()
