from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from voicecontrol.diagnostics.logs import read_recent_log_lines
from voicecontrol.diagnostics.microphone import run_microphone_test
from voicecontrol.diagnostics.executor_send import run_executor_send_test
from voicecontrol.diagnostics.stt_model_compare import run_stt_model_compare
from voicecontrol.diagnostics.store import DiagnosticResult, append_diagnostic_result
from voicecontrol.diagnostics.vad import run_vad_file_test
from voicecontrol.diagnostics.wake_word import run_wake_word_file_test
from voicecontrol.stt.engine import TranscriptionResult


class DiagnosticsTests(unittest.TestCase):
    def test_read_recent_log_lines_returns_tail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "voicecontrol.log"
            path.write_text("one\ntwo\nthree\n", encoding="utf-8")

            lines = read_recent_log_lines(path=path, max_lines=2)

        self.assertEqual(lines, ["two", "three"])

    def test_append_diagnostic_result_writes_json_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "diagnostics.jsonl"
            append_diagnostic_result(
                DiagnosticResult(name="microphone", status="ok", details={"rms": 0.5}),
                path=path,
            )
            data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["name"], "microphone")
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["details"]["rms"], 0.5)
        self.assertIn("created_at", data)

    def test_run_microphone_test_records_saves_and_reports_levels(self) -> None:
        audio = np.array([[0.0], [0.5], [-0.5]], dtype="float32")
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostic_path = Path(temp_dir) / "diagnostics.jsonl"
            wav_path = Path(temp_dir) / "mic.wav"

            with (
                patch("voicecontrol.diagnostics.microphone.record", return_value=audio) as record,
                patch("voicecontrol.diagnostics.microphone.save_wav", return_value=wav_path) as save_wav,
            ):
                result = run_microphone_test(
                    seconds=1.0,
                    wav_path=wav_path,
                    diagnostic_path=diagnostic_path,
                )

            saved = json.loads(diagnostic_path.read_text(encoding="utf-8"))

        record.assert_called_once()
        save_wav.assert_called_once()
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["wav_path"], str(wav_path))
        self.assertGreater(result.details["peak"], 0)
        self.assertEqual(saved["name"], "microphone")

    def test_run_vad_file_test_reports_detector_state(self) -> None:
        detector = Mock()
        detector.update.return_value = SimpleNamespace(
            speech_seconds=1.25,
            trailing_silence_seconds=0.5,
            speech_started=True,
            finished=True,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostic_path = Path(temp_dir) / "diagnostics.jsonl"
            with patch("voicecontrol.diagnostics.vad.sf.read", return_value=(np.ones(16000, dtype="float32"), 16000)):
                result = run_vad_file_test(
                    Path("sample.wav"),
                    detector=detector,
                    diagnostic_path=diagnostic_path,
                )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["speech_seconds"], 1.25)
        self.assertTrue(result.details["finished"])

    def test_run_wake_word_file_test_reports_max_score(self) -> None:
        detector = Mock()
        detector.score.side_effect = [0.1, 0.8]
        detector.threshold = 0.5
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostic_path = Path(temp_dir) / "diagnostics.jsonl"
            audio = np.ones(2560, dtype="int16")
            with patch("voicecontrol.diagnostics.wake_word.sf.read", return_value=(audio, 16000)):
                result = run_wake_word_file_test(
                    Path("wake.wav"),
                    detector=detector,
                    frame_samples=1280,
                    diagnostic_path=diagnostic_path,
                )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["max_score"], 0.8)
        self.assertTrue(result.details["detected"])

    def test_run_executor_send_test_can_paste_without_enter(self) -> None:
        driver = Mock()
        driver.app_name = "Trae"
        config = {"executor": {"default_target": "trae"}}
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostic_path = Path(temp_dir) / "diagnostics.jsonl"
            with patch(
                "voicecontrol.diagnostics.executor_send.create_driver_from_config",
                return_value=driver,
            ) as create_driver:
                result = run_executor_send_test(
                    config=config,
                    target="trae",
                    text="VoiceControl safe calibration",
                    auto_enter=False,
                    diagnostic_path=diagnostic_path,
                )

            saved = json.loads(diagnostic_path.read_text(encoding="utf-8"))

        create_driver.assert_called_once_with(config, "trae")
        driver.send_prompt.assert_called_once_with(
            "VoiceControl safe calibration",
            auto_enter=False,
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["target"], "trae")
        self.assertFalse(result.details["auto_enter"])
        self.assertEqual(saved["name"], "executor_send")

    def test_run_stt_model_compare_transcribes_each_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "command.wav"
            audio_path.write_bytes(b"wav")
            diagnostic_path = Path(temp_dir) / "diagnostics.jsonl"

            def make_engine(config: dict):
                stt_config = config["stt"]
                if stt_config["provider"] == "funasr_sensevoice":
                    model_name = "sensevoice_small"
                    engine_name = "funasr_sensevoice"
                else:
                    model_name = stt_config["whisper_model_size"]
                    engine_name = "faster_whisper"
                engine = Mock()
                engine.transcribe_file.return_value = TranscriptionResult(
                    text=f"{model_name} text",
                    engine=engine_name,
                    model=model_name,
                    language="zh",
                    language_probability=0.9,
                    duration_seconds=0.12,
                )
                return engine

            with patch(
                "voicecontrol.diagnostics.stt_model_compare.create_stt_engine",
                side_effect=make_engine,
            ) as create_engine:
                result = run_stt_model_compare(
                    audio_path,
                    diagnostic_path=diagnostic_path,
                )
            saved = json.loads(diagnostic_path.read_text(encoding="utf-8"))

        provider_calls = [call.args[0]["stt"]["provider"] for call in create_engine.call_args_list]
        whisper_sizes = [
            call.args[0]["stt"].get("whisper_model_size")
            for call in create_engine.call_args_list
            if call.args[0]["stt"]["provider"] == "faster_whisper"
        ]
        self.assertEqual(
            provider_calls,
            ["faster_whisper", "faster_whisper", "funasr_sensevoice"],
        )
        self.assertEqual(whisper_sizes, ["small", "medium"])
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.details["audio_path"], str(audio_path))
        self.assertEqual(result.details["models"]["small"]["text"], "small text")
        self.assertEqual(result.details["models"]["medium"]["text"], "medium text")
        self.assertEqual(
            result.details["models"]["sensevoice_small"]["text"],
            "sensevoice_small text",
        )
        self.assertEqual(saved["name"], "stt_model_compare")

    def test_run_stt_model_compare_keeps_whisper_results_when_sensevoice_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "command.wav"
            audio_path.write_bytes(b"wav")
            diagnostic_path = Path(temp_dir) / "diagnostics.jsonl"

            def make_engine(config: dict):
                stt_config = config["stt"]
                engine = Mock()
                if stt_config["provider"] == "funasr_sensevoice":
                    engine.transcribe_file.side_effect = RuntimeError(
                        "SenseVoice runtime is not installed or incomplete"
                    )
                    return engine

                model_size = stt_config["whisper_model_size"]
                engine.transcribe_file.return_value = TranscriptionResult(
                    text=f"{model_size} text",
                    engine="faster_whisper",
                    model=model_size,
                    language="zh",
                    duration_seconds=0.1,
                )
                return engine

            with patch(
                "voicecontrol.diagnostics.stt_model_compare.create_stt_engine",
                side_effect=make_engine,
            ):
                result = run_stt_model_compare(
                    audio_path,
                    diagnostic_path=diagnostic_path,
                )

        self.assertEqual(result.status, "error")
        self.assertIn("SenseVoice runtime is not installed", result.error)
        self.assertEqual(result.details["models"]["small"]["text"], "small text")
        self.assertEqual(result.details["models"]["medium"]["text"], "medium text")
        self.assertIn(
            "SenseVoice runtime is not installed",
            result.details["models"]["sensevoice_small"]["error"],
        )


if __name__ == "__main__":
    unittest.main()
