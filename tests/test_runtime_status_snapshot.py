from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from voicecontrol.events.status import StatusType
from voicecontrol.events.status_snapshot import (
    RuntimeStatusSnapshot,
    RuntimeStatusSnapshotStore,
    read_runtime_status,
    write_runtime_status,
)


class RuntimeStatusSnapshotTests(unittest.TestCase):
    def test_store_writes_status_snapshot_json_for_ui_polling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "runtime_status.json"
            store = RuntimeStatusSnapshotStore(path=path)

            store.publish(StatusType.RECORDING, message="recording now")
            store.publish(StatusType.SENDING, message="sending to Codex")
            store.publish(StatusType.ERROR, message="window not found")

            snapshot = read_runtime_status(path)

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(snapshot.current, "error")
        self.assertEqual(snapshot.message, "window not found")
        self.assertFalse(snapshot.is_recording)
        self.assertFalse(snapshot.is_sending)
        self.assertEqual(snapshot.last_error, "window not found")
        self.assertEqual([event["type"] for event in snapshot.recent_events], ["recording", "sending", "error"])
        self.assertIn("updated_at", snapshot.to_json_dict())

    def test_read_runtime_status_returns_none_for_missing_or_invalid_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.json"
            invalid = Path(temp_dir) / "runtime_status.json"
            invalid.write_text("{not valid json", encoding="utf-8")

            self.assertIsNone(read_runtime_status(missing))
            self.assertIsNone(read_runtime_status(invalid))

    def test_read_runtime_status_returns_none_for_invalid_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "runtime_status.json"
            path.write_text('{"updated_at": "not-a-timestamp"}', encoding="utf-8")

            self.assertIsNone(read_runtime_status(path))

    def test_store_serializes_concurrent_publishers(self) -> None:
        store = RuntimeStatusSnapshotStore(path=Path("runtime_status.json"))
        active_writers = 0
        max_active_writers = 0
        counter_lock = threading.Lock()

        def slow_write(_snapshot: RuntimeStatusSnapshot, _path: Path) -> Path:
            nonlocal active_writers, max_active_writers
            with counter_lock:
                active_writers += 1
                max_active_writers = max(max_active_writers, active_writers)
            time.sleep(0.02)
            with counter_lock:
                active_writers -= 1
            return Path("runtime_status.json")

        with patch("voicecontrol.events.status_snapshot.write_runtime_status", side_effect=slow_write):
            threads = [
                threading.Thread(target=store.publish, args=(StatusType.LISTENING, str(index)))
                for index in range(6)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        self.assertEqual(max_active_writers, 1)

    def test_runtime_status_writes_use_unique_temp_files(self) -> None:
        snapshot = RuntimeStatusSnapshot(current="listening")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "runtime_status.json"
            replaced_sources: list[Path] = []

            with patch(
                "voicecontrol.events.status_snapshot.os.replace",
                side_effect=lambda source, _target: replaced_sources.append(Path(source)),
            ):
                write_runtime_status(snapshot, path)
                write_runtime_status(snapshot, path)

        self.assertEqual(len(replaced_sources), 2)
        self.assertNotEqual(replaced_sources[0], replaced_sources[1])


if __name__ == "__main__":
    unittest.main()
