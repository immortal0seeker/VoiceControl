"""Wake-word model registry and path resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent / "models"

BUILTIN_WAKE_WORD_MODELS: tuple[str, ...] = ("hey_jarvis",)
BUNDLED_WAKE_WORD_MODELS: dict[str, Path] = {
    "world_activate": MODELS_DIR / "world_activate.onnx",
}


@dataclass(frozen=True)
class WakeWordModelSpec:
    """Resolved model information needed by openWakeWord."""

    name: str
    model_arg: str
    score_key: str


def available_wake_word_models() -> list[str]:
    """Return wake-word model names that can be selected in config/UI."""
    return [*BUILTIN_WAKE_WORD_MODELS, *BUNDLED_WAKE_WORD_MODELS.keys()]


def resolve_wake_word_model(model_name: str) -> WakeWordModelSpec:
    """Resolve a config model name to an openWakeWord model argument."""
    if model_name in BUILTIN_WAKE_WORD_MODELS:
        return WakeWordModelSpec(
            name=model_name,
            model_arg=model_name,
            score_key=model_name,
        )

    bundled_path = BUNDLED_WAKE_WORD_MODELS.get(model_name)
    if bundled_path is not None:
        return WakeWordModelSpec(
            name=model_name,
            model_arg=str(bundled_path),
            score_key=bundled_path.stem,
        )

    custom_path = Path(model_name)
    if custom_path.exists():
        return WakeWordModelSpec(
            name=custom_path.stem,
            model_arg=str(custom_path),
            score_key=custom_path.stem,
        )

    raise ValueError(f"Unknown wake-word model: {model_name}")
