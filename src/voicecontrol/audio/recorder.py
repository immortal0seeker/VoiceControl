"""Microphone recording and WAV saving.

Record audio from an input device and save/validate WAV files.
No STT, VAD, or wake-word logic here.
"""

from __future__ import annotations

import logging
import queue
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from voicecontrol.audio.device_manager import DeviceError, validate_device
from voicecontrol.config import settings

logger = logging.getLogger(__name__)


class RecordingError(RuntimeError):
    """Raised when audio capture fails."""


def record(
    seconds: float = settings.DEFAULT_RECORD_SECONDS,
    sample_rate: int = settings.SAMPLE_RATE,
    channels: int = settings.CHANNELS,
    device: int | None = settings.INPUT_DEVICE,
) -> np.ndarray:
    """Record ``seconds`` of audio and return it as a float32 numpy array.

    Raises ``RecordingError`` if the device is unusable or capture fails.
    """
    if seconds <= 0:
        raise RecordingError(f"Recording duration must be positive, got {seconds}.")

    selected = validate_device(device)
    logger.info(
        "Recording %.1fs from device [%d] %s (%d Hz, %d ch)",
        seconds, selected.index, selected.name, sample_rate, channels,
    )

    frames = int(seconds * sample_rate)
    try:
        audio = sd.rec(
            frames,
            samplerate=sample_rate,
            channels=channels,
            dtype=settings.DTYPE,
            device=selected.index,
        )
        sd.wait()
    except Exception as exc:
        raise RecordingError(f"Audio capture failed: {exc}") from exc

    return audio


def save_wav(
    audio: np.ndarray,
    path: str | Path = settings.DEFAULT_RECORDING_PATH,
    sample_rate: int = settings.SAMPLE_RATE,
) -> Path:
    """Save an audio array to ``path`` as a WAV file, creating dirs as needed."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        sf.write(out_path, audio, sample_rate)
    except Exception as exc:
        raise RecordingError(f"Failed to write WAV to {out_path}: {exc}") from exc

    logger.info("Saved recording to %s", out_path)
    return out_path


def record_to_file(
    seconds: float = settings.DEFAULT_RECORD_SECONDS,
    path: str | Path = settings.DEFAULT_RECORDING_PATH,
    sample_rate: int = settings.SAMPLE_RATE,
    channels: int = settings.CHANNELS,
    device: int | None = settings.INPUT_DEVICE,
) -> Path:
    """Record audio and save it to a WAV file in one call."""
    audio = record(seconds, sample_rate, channels, device)
    return save_wav(audio, path, sample_rate)


class StreamRecorder:
    """Open-ended recording: ``start()`` then ``stop()`` at any time.

    Used by the hotkey-driven flow where the duration is unknown in advance.
    advance. Audio is captured on PortAudio's callback thread and collected
    into memory until ``stop()`` is called.
    """

    def __init__(
        self,
        sample_rate: int = settings.SAMPLE_RATE,
        channels: int = settings.CHANNELS,
        device: int | None = settings.INPUT_DEVICE,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self._chunks: list[np.ndarray] = []
        self._read_chunks = 0
        self._stream: sd.InputStream | None = None

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            logger.warning("Input stream status: %s", status)
        self._chunks.append(indata.copy())

    def start(self) -> None:
        """Open the input stream and begin capturing."""
        if self._stream is not None:
            raise RecordingError("Recording already in progress.")

        selected = validate_device(self.device)
        self._chunks = []
        self._read_chunks = 0
        logger.info(
            "Stream recording from device [%d] %s (%d Hz, %d ch)",
            selected.index, selected.name, self.sample_rate, self.channels,
        )
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=settings.DTYPE,
                device=selected.index,
                callback=self._callback,
            )
            self._stream.start()
        except Exception as exc:
            self._stream = None
            raise RecordingError(f"Failed to open input stream: {exc}") from exc

    # Early VAD read the full buffer each poll; replaced by read_new(). Kept commented
    # in case a one-shot "audio so far" debug helper is needed again.
    # def snapshot(self) -> np.ndarray:
    #     """Return audio captured so far without stopping the stream."""
    #     chunks = list(self._chunks)  # copy ref; appends are GIL-atomic
    #     if not chunks:
    #         return np.empty((0, self.channels), dtype=settings.DTYPE)
    #     return np.concatenate(chunks, axis=0)

    def read_new(self) -> np.ndarray:
        """Return only samples captured since the previous ``read_new`` call.

        Lets a streaming consumer (e.g. the VAD endpoint detector) process each
        sample exactly once instead of re-reading the whole growing buffer.
        """
        available = len(self._chunks)  # snapshot length; appends are GIL-atomic
        new_chunks = self._chunks[self._read_chunks:available]
        self._read_chunks = available
        if not new_chunks:
            return np.empty((0, self.channels), dtype=settings.DTYPE)
        return np.concatenate(new_chunks, axis=0)

    def stop(self) -> np.ndarray:
        """Stop capturing and return the recorded audio as a float32 array."""
        if self._stream is None:
            raise RecordingError("No recording in progress.")

        try:
            self._stream.stop()
            self._stream.close()
        except Exception as exc:
            raise RecordingError(f"Failed to close input stream: {exc}") from exc
        finally:
            self._stream = None

        if not self._chunks:
            return np.empty((0, self.channels), dtype=settings.DTYPE)
        return np.concatenate(self._chunks, axis=0)


class MicFrameStream:
    """Yield fixed-size mic frames in real time, dropping history.

    Unlike ``StreamRecorder`` (which keeps everything), this is for always-on
    consumers like wake-word detection: frames flow through a small bounded
    queue and are dropped if the consumer falls behind. Use as a context
    manager and pull frames with :meth:`read`.
    """

    def __init__(
        self,
        frame_samples: int,
        sample_rate: int = settings.SAMPLE_RATE,
        channels: int = settings.CHANNELS,
        device: int | None = settings.INPUT_DEVICE,
        dtype: str = "int16",
        max_queued: int = 50,
    ) -> None:
        self.frame_samples = frame_samples
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.dtype = dtype
        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=max_queued)
        self._stream: sd.InputStream | None = None

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            logger.warning("Mic frame stream status: %s", status)
        try:
            self._queue.put_nowait(indata.copy())
        except queue.Full:
            pass  # consumer is behind; drop the frame

    def __enter__(self) -> MicFrameStream:
        selected = validate_device(self.device)
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                device=selected.index,
                blocksize=self.frame_samples,
                callback=self._callback,
            )
            self._stream.start()
        except Exception as exc:
            self._stream = None
            raise RecordingError(f"Failed to open mic frame stream: {exc}") from exc
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def read(self, timeout: float = 0.5) -> np.ndarray | None:
        """Return the next frame as a 1D array, or ``None`` if none arrived."""
        try:
            frame = self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
        return frame.reshape(-1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        print(f"Recording {settings.DEFAULT_RECORD_SECONDS}s — speak now...")
        saved = record_to_file()
        print(f"Done. WAV saved to: {saved}")
    except (DeviceError, RecordingError) as exc:
        print(f"ERROR: {exc}")
