from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from voicecontrol.audio.recorder import MicFrameStream, RecordingError, StreamRecorder


class AudioStreamCleanupTests(unittest.TestCase):
    def test_stream_recorder_closes_stream_when_start_fails(self) -> None:
        stream = Mock()
        stream.start.side_effect = RuntimeError("start failed")

        with (
            patch(
                "voicecontrol.audio.recorder.validate_device",
                return_value=SimpleNamespace(index=1, name="Mic"),
            ),
            patch("voicecontrol.audio.recorder.sd.InputStream", return_value=stream),
        ):
            recorder = StreamRecorder()
            with self.assertRaises(RecordingError):
                recorder.start()

        stream.close.assert_called_once_with()

    def test_stream_recorder_closes_stream_when_stop_fails(self) -> None:
        stream = Mock()
        stream.stop.side_effect = RuntimeError("stop failed")
        recorder = StreamRecorder()
        recorder._stream = stream

        with self.assertRaises(RecordingError):
            recorder.stop()

        stream.close.assert_called_once_with()
        self.assertIsNone(recorder._stream)

    def test_mic_frame_stream_closes_stream_when_start_fails(self) -> None:
        stream = Mock()
        stream.start.side_effect = RuntimeError("start failed")

        with (
            patch(
                "voicecontrol.audio.recorder.validate_device",
                return_value=SimpleNamespace(index=1, name="Mic"),
            ),
            patch("voicecontrol.audio.recorder.sd.InputStream", return_value=stream),
        ):
            mic = MicFrameStream(frame_samples=128)
            with self.assertRaises(RecordingError):
                mic.__enter__()

        stream.close.assert_called_once_with()

    def test_mic_frame_stream_closes_stream_when_context_stop_fails(self) -> None:
        stream = Mock()
        stream.stop.side_effect = RuntimeError("stop failed")
        mic = MicFrameStream(frame_samples=128)
        mic._stream = stream

        with self.assertRaises(RuntimeError):
            mic.__exit__(None, None, None)

        stream.close.assert_called_once_with()
        self.assertIsNone(mic._stream)


if __name__ == "__main__":
    unittest.main()
