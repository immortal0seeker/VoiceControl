from __future__ import annotations

import unittest
from pathlib import Path


MOJIBAKE_MARKERS = [
    "鎴",
    "鏄",
    "鍚",
    "鈫",
    "銆",
    "鐘",
    "褰",
    "鏃",
    "楹",
    "鍞",
    "鐩",
    "璁",
    "绐",
]

SCANNED_SUFFIXES = {".py", ".md", ".json", ".toml", ".txt"}
SKIPPED_DIRS = {".git", ".venv", "__pycache__", "audio_files", "logs"}


class NoMojibakeTests(unittest.TestCase):
    def test_text_files_do_not_contain_common_mojibake_markers(self) -> None:
        root = Path(__file__).resolve().parents[1]
        offenders: list[str] = []

        for path in root.rglob("*"):
            if any(part in SKIPPED_DIRS for part in path.parts):
                continue
            if path == Path(__file__).resolve():
                continue
            if not path.is_file() or path.suffix.lower() not in SCANNED_SUFFIXES:
                continue

            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                hits = sorted({marker for marker in MOJIBAKE_MARKERS if marker in line})
                if hits:
                    rel_path = path.relative_to(root)
                    offenders.append(f"{rel_path}:{line_number}: {''.join(hits)}")

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
