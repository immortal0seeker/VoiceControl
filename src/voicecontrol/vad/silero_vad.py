"""Voice activity detection using the Silero VAD ONNX model.

Reuses the ``silero_vad_v6.onnx`` model bundled with faster-whisper and runs
it through onnxruntime — no extra dependency, no PyTorch.

Given mono 16 kHz float32 audio, report per-frame speech probability and
decide when an utterance has ended (trailing silence). No mic or recording
logic here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from faster_whisper.vad import get_vad_model

from voicecontrol.config import settings

logger = logging.getLogger(__name__)

# The Silero model consumes fixed 512-sample windows at 16 kHz (32 ms/frame).
FRAME_SAMPLES = 512


class SileroVad:
    """Thin wrapper computing per-frame speech probabilities."""

    def __init__(self, sample_rate: int = settings.SAMPLE_RATE) -> None:
        if sample_rate != 16000:
            raise ValueError("Silero VAD requires a 16 kHz sample rate.")
        self.sample_rate = sample_rate
        self._model = get_vad_model()

    def speech_probs(self, audio: np.ndarray) -> np.ndarray:
        """Return one speech probability per 512-sample frame.

        ``audio`` must be mono float32; it is right-padded to a multiple of
        the frame size. Returns an empty array for sub-frame input.
        """
        if audio.ndim > 1:
            audio = audio.reshape(-1)
        audio = audio.astype("float32", copy=False)

        if audio.shape[0] < FRAME_SAMPLES:
            return np.empty(0, dtype="float32")

        remainder = audio.shape[0] % FRAME_SAMPLES
        if remainder:
            audio = np.pad(audio, (0, FRAME_SAMPLES - remainder))

        out = self._model(audio, num_samples=FRAME_SAMPLES)
        return np.asarray(out, dtype="float32").reshape(-1)


@dataclass(frozen=True)
class EndpointState:
    """Result of evaluating the buffer captured so far."""

    speech_started: bool
    finished: bool
    speech_seconds: float
    trailing_silence_seconds: float


class EndpointDetector:
    """Decides when speech has started and then ended (trailing silence).

    Feed new audio through ``update`` for streaming use, or call ``evaluate``
    once for a complete clip.
    """

    def __init__(
        self,
        vad: SileroVad | None = None,
        speech_threshold: float = settings.VAD_SPEECH_THRESHOLD,
        silence_duration: float = settings.VAD_SILENCE_DURATION,
        min_speech_duration: float = settings.VAD_MIN_SPEECH_DURATION,
    ) -> None:
        self.vad = vad or SileroVad()
        self.speech_threshold = speech_threshold
        self.silence_duration = silence_duration
        self.min_speech_duration = min_speech_duration
        self._frame_seconds = FRAME_SAMPLES / self.vad.sample_rate
        self.reset()

    def reset(self) -> None:
        """Clear streaming state so the detector can be reused for a new clip."""
        self._leftover = np.empty(0, dtype="float32")
        self._speech_frames = 0
        self._trailing_silence_frames = 0

    def _state(self) -> EndpointState:
        speech_seconds = self._speech_frames * self._frame_seconds
        speech_started = speech_seconds >= self.min_speech_duration
        trailing_silence_seconds = self._trailing_silence_frames * self._frame_seconds
        finished = speech_started and trailing_silence_seconds >= self.silence_duration
        return EndpointState(
            speech_started=speech_started,
            finished=finished,
            speech_seconds=speech_seconds,
            trailing_silence_seconds=trailing_silence_seconds,
        )

    def update(self, new_audio: np.ndarray) -> EndpointState:
        """Feed newly captured samples and return the updated endpoint state.

        Only complete 512-sample frames are scored; a short remainder is buffered
        until the next call. Each frame is processed exactly once, so a full
        utterance costs O(n) instead of re-scoring the whole buffer each poll.
        """
        if new_audio.ndim > 1:
            new_audio = new_audio.reshape(-1)
        new_audio = new_audio.astype("float32", copy=False)

        buf = (
            np.concatenate([self._leftover, new_audio])
            if self._leftover.size
            else new_audio
        )
        n_complete = (buf.shape[0] // FRAME_SAMPLES) * FRAME_SAMPLES
        if n_complete:
            probs = self.vad.speech_probs(buf[:n_complete])
            for is_speech in (probs >= self.speech_threshold).tolist():
                if is_speech:
                    self._speech_frames += 1
                    self._trailing_silence_frames = 0
                else:
                    self._trailing_silence_frames += 1
        self._leftover = buf[n_complete:].copy()
        return self._state()

    def evaluate(self, audio: np.ndarray) -> EndpointState:
        """One-shot endpoint assessment over a whole buffer (resets state)."""
        self.reset()
        return self.update(audio)

    def is_finished(self, audio: np.ndarray) -> bool:
        """Convenience: True once speech was seen and trailing silence elapsed."""
        return self.evaluate(audio).finished


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    import soundfile as sf

    wav = settings.DEFAULT_RECORDING_PATH
    audio, sr = sf.read(wav, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]
    vad = SileroVad()
    probs = vad.speech_probs(audio)
    frame_s = FRAME_SAMPLES / sr
    speech_frames = int((probs >= settings.VAD_SPEECH_THRESHOLD).sum())
    print(f"file: {wav}")
    print(f"frames: {probs.size} ({frame_s * 1000:.0f} ms each)")
    print(f"speech frames: {speech_frames} ({speech_frames * frame_s:.2f} s)")
    print(f"max prob: {probs.max():.2f}  mean prob: {probs.mean():.2f}")
