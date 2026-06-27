from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from voicecontrol.events.status import StatusType
from voicecontrol.events.status_snapshot import RuntimeStatusSnapshotStore, read_runtime_status


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


if __name__ == "__main__":
    unittest.main()
