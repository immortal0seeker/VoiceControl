from __future__ import annotations

from voicecontrol.stt.engine import TranscriptionResult


def test_transcription_result_exposes_history_metadata() -> None:
    result = TranscriptionResult(
        text="打开项目",
        engine="faster_whisper",
        model="small",
        language="zh",
        language_probability=0.93,
    )

    assert result.text == "打开项目"
    assert result.engine == "faster_whisper"
    assert result.model == "small"
    assert result.to_history_metadata() == {
        "stt_engine": "faster_whisper",
        "stt_model": "small",
        "stt_language": "zh",
        "stt_language_probability": 0.93,
    }
