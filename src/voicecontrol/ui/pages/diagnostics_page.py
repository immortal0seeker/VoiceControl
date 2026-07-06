"""Diagnostic pages for the VoiceControl settings UI."""

from __future__ import annotations

from collections.abc import Callable
import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from voicecontrol.diagnostics.executor_send import run_executor_send_test
from voicecontrol.diagnostics.microphone import run_microphone_test
from voicecontrol.diagnostics.stt_model_compare import run_stt_model_compare
from voicecontrol.diagnostics.store import DiagnosticResult
from voicecontrol.diagnostics.vad import run_vad_file_test
from voicecontrol.diagnostics.wake_word import run_wake_word_file_test
from voicecontrol.tts.speaker import TextSpeaker, TtsError
from voicecontrol.ui.pages.base import page_layout
from voicecontrol.ui.widgets import card, line_edit

logger = logging.getLogger(__name__)


def _make_selectable(label: QLabel) -> QLabel:
    label.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse
        | Qt.TextInteractionFlag.TextSelectableByKeyboard
    )
    return label


def _format_diagnostic_result(result: DiagnosticResult) -> str:
    details = ", ".join(f"{key}={value}" for key, value in result.details.items())
    parts = [result.status]
    if details:
        parts.append(details)
    if result.error:
        parts.append(result.error)
    return "：".join(parts)


class MicrophoneDiagnosticsPage(QWidget):
    """Records a short clip and checks input levels."""

    def __init__(self, diagnostic_path: Path | None = None) -> None:
        super().__init__()
        self.setObjectName("microphoneDiagnosticsPage")
        self._diagnostic_path = diagnostic_path

        root_layout = page_layout(self, "麦克风诊断", "录制短音频并检查输入电平。")

        run_button = QPushButton("开始测试")
        run_button.setObjectName("runMicrophoneDiagnosticButton")
        self._result_label = _make_selectable(QLabel("尚未运行。"))
        self._result_label.setObjectName("microphoneDiagnosticResultLabel")
        self._result_label.setWordWrap(True)
        root_layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        root_layout.addWidget(self._result_label)
        root_layout.addStretch(1)

        run_button.clicked.connect(self._run)

    def _run(self) -> None:
        result = run_microphone_test(diagnostic_path=self._diagnostic_path)
        self._result_label.setText(_format_diagnostic_result(result))


class VadTestPage(QWidget):
    """Selects a WAV file and checks VAD endpointing results."""

    def __init__(self, diagnostic_path: Path | None = None) -> None:
        super().__init__()
        self.setObjectName("vadTestPage")
        self._diagnostic_path = diagnostic_path

        root_layout = page_layout(self, "VAD 测试", "选择 WAV 文件并检查端点检测结果。")

        self._file_path = line_edit("", "WAV 文件路径")
        self._file_path.setObjectName("vadTestFilePath")
        run_button = QPushButton("运行 VAD 测试")
        run_button.setObjectName("runVadTestButton")
        self._result_label = _make_selectable(QLabel("尚未运行。"))
        self._result_label.setObjectName("vadTestResultLabel")
        self._result_label.setWordWrap(True)
        root_layout.addWidget(self._file_path)
        root_layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        root_layout.addWidget(self._result_label)
        root_layout.addStretch(1)

        run_button.clicked.connect(self._run)

    def _run(self) -> None:
        wav_path = self._file_path.text().strip()
        if not wav_path:
            self._result_label.setText("error：请先填写 WAV 文件路径。")
            return
        result = run_vad_file_test(wav_path, diagnostic_path=self._diagnostic_path)
        self._result_label.setText(_format_diagnostic_result(result))


class WakeWordTestPage(QWidget):
    """Selects a WAV file and checks wake-word scores."""

    def __init__(self, diagnostic_path: Path | None = None) -> None:
        super().__init__()
        self.setObjectName("wakeWordTestPage")
        self._diagnostic_path = diagnostic_path

        root_layout = page_layout(self, "唤醒词测试", "选择 WAV 文件并检查唤醒词得分。")

        self._file_path = line_edit("", "WAV 文件路径")
        self._file_path.setObjectName("wakeWordTestFilePath")
        run_button = QPushButton("运行唤醒词测试")
        run_button.setObjectName("runWakeWordTestButton")
        self._result_label = _make_selectable(QLabel("尚未运行。"))
        self._result_label.setObjectName("wakeWordTestResultLabel")
        self._result_label.setWordWrap(True)
        root_layout.addWidget(self._file_path)
        root_layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        root_layout.addWidget(self._result_label)
        root_layout.addStretch(1)

        run_button.clicked.connect(self._run)

    def _run(self) -> None:
        wav_path = self._file_path.text().strip()
        if not wav_path:
            self._result_label.setText("error：请先填写 WAV 文件路径。")
            return
        result = run_wake_word_file_test(wav_path, diagnostic_path=self._diagnostic_path)
        self._result_label.setText(_format_diagnostic_result(result))


class DiagnosticsPage(QWidget):
    """Combined diagnostics page for microphone, VAD, and wake-word checks."""

    def __init__(self, diagnostic_path: Path | None = None, config: dict | None = None) -> None:
        super().__init__()
        self.setObjectName("diagnosticsPage")
        self._diagnostic_path = diagnostic_path
        self._config = config or {}

        root_layout = page_layout(self, "诊断", "集中运行麦克风、VAD 和唤醒词测试。")
        root_layout.setSpacing(16)
        scroll = QScrollArea()
        scroll.setObjectName("diagnosticsScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        self._add_microphone_card(content_layout)
        self._add_vad_card(content_layout)
        self._add_wake_word_card(content_layout)
        self._add_stt_card(content_layout)
        self._add_tts_card(content_layout)
        self._add_executor_card(content_layout)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

    def _add_microphone_card(self, root_layout: QVBoxLayout) -> None:
        frame, layout = card("麦克风")
        run_button = QPushButton("开始测试")
        run_button.setObjectName("runMicrophoneDiagnosticButton")
        self._microphone_run_button = run_button
        self._microphone_result_label = _make_selectable(QLabel("尚未运行。"))
        self._microphone_result_label.setObjectName("microphoneDiagnosticResultLabel")
        self._microphone_result_label.setWordWrap(True)
        layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._microphone_result_label)
        root_layout.addWidget(frame)
        run_button.clicked.connect(self._run_microphone)

    def _add_vad_card(self, root_layout: QVBoxLayout) -> None:
        frame, layout = card("VAD 文件测试")
        self._vad_file_path = line_edit("", "WAV 文件路径")
        self._vad_file_path.setObjectName("vadTestFilePath")
        run_button = QPushButton("运行 VAD 测试")
        run_button.setObjectName("runVadTestButton")
        self._vad_run_button = run_button
        self._vad_result_label = _make_selectable(QLabel("尚未运行。"))
        self._vad_result_label.setObjectName("vadTestResultLabel")
        self._vad_result_label.setWordWrap(True)
        layout.addWidget(self._vad_file_path)
        layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._vad_result_label)
        root_layout.addWidget(frame)
        run_button.clicked.connect(self._run_vad)

    def _add_wake_word_card(self, root_layout: QVBoxLayout) -> None:
        frame, layout = card("唤醒词文件测试")
        self._wake_word_file_path = line_edit("", "WAV 文件路径")
        self._wake_word_file_path.setObjectName("wakeWordTestFilePath")
        run_button = QPushButton("运行唤醒词测试")
        run_button.setObjectName("runWakeWordTestButton")
        self._wake_word_run_button = run_button
        self._wake_word_result_label = _make_selectable(QLabel("尚未运行。"))
        self._wake_word_result_label.setObjectName("wakeWordTestResultLabel")
        self._wake_word_result_label.setWordWrap(True)
        layout.addWidget(self._wake_word_file_path)
        layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._wake_word_result_label)
        root_layout.addWidget(frame)
        run_button.clicked.connect(self._run_wake_word)

    def _add_stt_card(self, root_layout: QVBoxLayout) -> None:
        frame, layout = card("STT 模型对比")
        run_button = QPushButton("用最近录音比较 small / medium / SenseVoice-Small")
        run_button.setObjectName("runSttModelCompareButton")
        self._stt_compare_run_button = run_button
        self._stt_compare_result_label = _make_selectable(QLabel("尚未运行。"))
        self._stt_compare_result_label.setObjectName("sttModelCompareResultLabel")
        self._stt_compare_result_label.setWordWrap(True)
        layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._stt_compare_result_label)
        root_layout.addWidget(frame)
        run_button.clicked.connect(self._run_stt_compare)

    def _add_tts_card(self, root_layout: QVBoxLayout) -> None:
        frame, layout = card("TTS 状态提示")
        run_button = QPushButton("测试 TTS")
        run_button.setObjectName("backgroundTestTtsButton")
        self._tts_result_label = _make_selectable(QLabel("尚未运行。"))
        self._tts_result_label.setObjectName("ttsDiagnosticResultLabel")
        self._tts_result_label.setWordWrap(True)
        layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._tts_result_label)
        root_layout.addWidget(frame)
        run_button.clicked.connect(self._run_tts)

    def _add_executor_card(self, root_layout: QVBoxLayout) -> None:
        frame, layout = card("目标应用发送")
        draft_button = QPushButton("只粘贴不回车")
        draft_button.setObjectName("testPasteToTargetDraftButton")
        run_button = QPushButton("粘贴并发送到当前目标")
        run_button.setObjectName("testSendToCodexButton")
        self._codex_result_label = _make_selectable(QLabel("尚未运行。"))
        self._codex_result_label.setObjectName("codexSendDiagnosticResultLabel")
        self._codex_result_label.setWordWrap(True)
        layout.addWidget(draft_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._codex_result_label)
        root_layout.addWidget(frame)
        draft_button.clicked.connect(lambda: self._run_executor_send(auto_enter=False))
        run_button.clicked.connect(lambda: self._run_executor_send(auto_enter=True))

    def _run_microphone(self) -> None:
        self._run_diagnostic(
            self._microphone_run_button,
            self._microphone_result_label,
            lambda: run_microphone_test(diagnostic_path=self._diagnostic_path),
        )

    def _run_vad(self) -> None:
        wav_path = self._vad_file_path.text().strip()
        if not wav_path:
            self._vad_result_label.setText("error：请先填写 WAV 文件路径。")
            return
        self._run_diagnostic(
            self._vad_run_button,
            self._vad_result_label,
            lambda: run_vad_file_test(wav_path, diagnostic_path=self._diagnostic_path),
        )

    def _run_wake_word(self) -> None:
        wav_path = self._wake_word_file_path.text().strip()
        if not wav_path:
            self._wake_word_result_label.setText("error：请先填写 WAV 文件路径。")
            return
        self._run_diagnostic(
            self._wake_word_run_button,
            self._wake_word_result_label,
            lambda: run_wake_word_file_test(wav_path, diagnostic_path=self._diagnostic_path),
        )

    def _run_stt_compare(self) -> None:
        self._run_diagnostic(
            self._stt_compare_run_button,
            self._stt_compare_result_label,
            lambda: run_stt_model_compare(diagnostic_path=self._diagnostic_path),
        )

    def _run_tts(self) -> None:
        try:
            tts_config = self._config.get("tts", {})
            TextSpeaker(
                enabled=True,
                rate=int(tts_config.get("rate", 0)),
                volume=int(tts_config.get("volume", 100)),
                voice=tts_config.get("voice"),
            ).speak("我在")
        except (TtsError, ValueError, TypeError) as exc:
            self._tts_result_label.setText(f"TTS 测试失败：{exc}")
            return
        self._tts_result_label.setText("TTS 测试已发送。")

    def _run_executor_send(self, *, auto_enter: bool) -> None:
        result = run_executor_send_test(
            config=self._config,
            target=None,
            auto_enter=auto_enter,
            diagnostic_path=self._diagnostic_path,
        )
        self._codex_result_label.setText(_format_diagnostic_result(result))

    def _run_diagnostic(
        self,
        button: QPushButton,
        result_label: QLabel,
        runner: Callable[[], DiagnosticResult],
    ) -> None:
        button.setEnabled(False)
        result_label.setText("运行中…")
        try:
            result = runner()
            result_label.setText(_format_diagnostic_result(result))
        except Exception as exc:
            logger.debug("Diagnostic action failed.", exc_info=True)
            result_label.setText(f"error：{exc}")
        finally:
            button.setEnabled(True)
