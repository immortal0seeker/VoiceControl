from __future__ import annotations

from pathlib import Path

import pytest

from voicecontrol.stt.sensevoice_engine import SenseVoiceEngine, SenseVoiceError


class FakeSenseVoiceModel:
    def __init__(self) -> None:
        self.generate_calls: list[dict[str, object]] = []

    def generate(self, **kwargs: object) -> list[dict[str, str]]:
        self.generate_calls.append(kwargs)
        return [{"text": "<|zh|><|NEUTRAL|><|Speech|>我在测试"}]


def test_sensevoice_engine_loads_lazily_and_transcribes_file(tmp_path: Path) -> None:
    audio_path = tmp_path / "command.wav"
    audio_path.write_bytes(b"fake wav")
    fake_model = FakeSenseVoiceModel()
    factory_calls: list[dict[str, object]] = []

    def automodel_factory(**kwargs: object) -> FakeSenseVoiceModel:
        factory_calls.append(kwargs)
        return fake_model

    engine = SenseVoiceEngine(
        model="SenseVoiceSmall",
        device="cpu",
        language="zh",
        automodel_factory=automodel_factory,
    )

    result = engine.transcribe_file(audio_path)

    assert factory_calls == [
        {
            "model": "iic/SenseVoiceSmall",
            "vad_model": "fsmn-vad",
            "vad_kwargs": {"max_single_segment_time": 30000},
            "device": "cpu",
            "disable_update": True,
        }
    ]
    assert fake_model.generate_calls == [
        {"input": str(audio_path), "batch_size": 1, "language": "zh"}
    ]
    assert result.text == "我在测试"
    assert result.engine == "funasr_sensevoice"
    assert result.model == "SenseVoiceSmall"
    assert result.language == "zh"
    assert result.duration_seconds is not None


def test_sensevoice_engine_reuses_loaded_model(tmp_path: Path) -> None:
    audio_path = tmp_path / "command.wav"
    audio_path.write_bytes(b"fake wav")
    fake_model = FakeSenseVoiceModel()
    load_count = 0

    def automodel_factory(**kwargs: object) -> FakeSenseVoiceModel:
        nonlocal load_count
        load_count += 1
        return fake_model

    engine = SenseVoiceEngine(automodel_factory=automodel_factory)

    engine.transcribe_file(audio_path)
    engine.transcribe_file(audio_path)

    assert load_count == 1


def test_sensevoice_engine_reports_missing_runtime() -> None:
    def missing_runtime_factory(**kwargs: object) -> object:
        raise ModuleNotFoundError("No module named 'funasr'")

    engine = SenseVoiceEngine(automodel_factory=missing_runtime_factory)

    with pytest.raises(SenseVoiceError, match="SenseVoice runtime is not installed"):
        engine.load()


def test_sensevoice_engine_rejects_cuda_when_pytorch_cuda_is_unavailable() -> None:
    engine = SenseVoiceEngine(
        device="cuda",
        cuda_available=lambda: False,
        automodel_factory=lambda **kwargs: FakeSenseVoiceModel(),
    )

    with pytest.raises(SenseVoiceError, match="CUDA-enabled PyTorch"):
        engine.load()


def test_sensevoice_engine_rejects_missing_audio_file(tmp_path: Path) -> None:
    engine = SenseVoiceEngine(automodel_factory=lambda **kwargs: FakeSenseVoiceModel())

    with pytest.raises(SenseVoiceError, match="Audio file not found"):
        engine.transcribe_file(tmp_path / "missing.wav")
