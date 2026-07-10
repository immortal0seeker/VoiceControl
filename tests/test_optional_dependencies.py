from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class OptionalDependenciesTests(unittest.TestCase):
    def test_sensevoice_runtime_is_optional_extra(self) -> None:
        data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        dependencies = data["project"]["dependencies"]
        normalized_dependencies = "\n".join(dependencies).lower()
        self.assertNotIn("funasr", normalized_dependencies)
        self.assertNotIn("torch", normalized_dependencies)
        self.assertNotIn("torchaudio", normalized_dependencies)

        sensevoice_extra = data["project"]["optional-dependencies"]["sensevoice"]
        normalized_extra = "\n".join(sensevoice_extra).lower()
        self.assertIn("funasr", normalized_extra)
        self.assertIn("torch", normalized_extra)
        self.assertIn("torchaudio", normalized_extra)
        self.assertIn("modelscope", normalized_extra)


if __name__ == "__main__":
    unittest.main()
