"""Wake word detection using openWakeWord.

Wraps an openWakeWord model and reports a per-frame score for the configured
wake word. Runs on bundled ONNX models via onnxruntime — no PyTorch, no
account/key. The wake word only *gates* activation; the command spoken after
it can still be Chinese (handled later by the STT module).

Scores audio frames for the wake word. No mic, STT, or executor logic here.
"""

from __future__ import annotations

import logging

import numpy as np
from openwakeword.model import Model

from voicecontrol.config import settings

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Scores 1280-sample (80 ms) int16 frames for the configured wake word."""

    def __init__(
        self,
        model_name: str = settings.WAKE_WORD_MODEL,
        threshold: float = settings.WAKE_THRESHOLD,
        inference_framework: str = settings.WAKE_INFERENCE_FRAMEWORK,
    ) -> None:
        self.model_name = model_name
        self.threshold = threshold
        logger.info("Loading wake word model '%s' (%s)", model_name, inference_framework)
        self._model = Model(
            wakeword_models=[model_name],
            inference_framework=inference_framework,
        )

    def reset(self) -> None:
        """Clear internal audio buffers between listening sessions."""
        self._model.reset()

    def score(self, frame: np.ndarray) -> float:
        """Return the wake-word probability for one int16 frame."""
        if frame.dtype != np.int16:
            frame = frame.astype(np.int16)
        scores = self._model.predict(frame)
        return float(scores.get(self.model_name, 0.0))

    def is_wake(self, frame: np.ndarray) -> bool:
        """Convenience: True if the frame's score crosses the threshold."""
        return self.score(frame) >= self.threshold


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from voicecontrol.audio.recorder import MicFrameStream

    detector = WakeWordDetector()
    print(f"Listening for wake word '{detector.model_name}' — say it. Ctrl+C to stop.")
    peak = 0.0
    try:
        with MicFrameStream(settings.WAKE_FRAME_SAMPLES, dtype="int16") as mic:
            detector.reset()
            while True:
                frame = mic.read(timeout=0.5)
                if frame is None:
                    continue
                s = detector.score(frame)
                peak = max(peak, s)
                if s >= detector.threshold:
                    print(f"  WAKE! score={s:.2f}")
                    peak = 0.0
    except KeyboardInterrupt:
        print(f"\nStopped. Peak score seen: {peak:.2f}")
