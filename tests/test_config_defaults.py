from __future__ import annotations

import unittest

from voicecontrol.config.manager import CONFIG_PATH, load_config


class CheckedInConfigTests(unittest.TestCase):
    def test_checked_in_vad_max_record_seconds_allows_long_voice_commands(self) -> None:
        config = load_config(CONFIG_PATH)

        self.assertEqual(config["vad"]["max_record_seconds"], 180.0)


if __name__ == "__main__":
    unittest.main()
