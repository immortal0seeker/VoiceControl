from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from voicecontrol.config.manager import CONFIG_PATH, DEFAULT_CONFIG, load_config, save_config
from voicecontrol.config import settings
from voicecontrol.control.commands import CONTROL_COMMAND_PATH, CONTROL_RESPONSE_PATH


class CheckedInConfigTests(unittest.TestCase):
    def test_save_config_uses_atomic_same_directory_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            real_replace = os.replace
            with patch(
                "voicecontrol.config.manager.os.replace",
                side_effect=real_replace,
            ) as replace:
                save_config({"audio": {"input_device": None}}, path)

            source, target = replace.call_args.args
            self.assertEqual(Path(source).parent, path.parent)
            self.assertEqual(Path(target), path)
            self.assertIsNone(load_config(path)["audio"]["input_device"])

    def test_checked_in_vad_max_record_seconds_allows_long_voice_commands(self) -> None:
        config = load_config(CONFIG_PATH)

        self.assertEqual(config["vad"]["max_record_seconds"], 180.0)

    def test_checked_in_config_has_tts_defaults(self) -> None:
        config = load_config(CONFIG_PATH)

        self.assertEqual(
            config["tts"],
            {
                "enabled": True,
                "rate": 0,
                "volume": 100,
                "voice": None,
            },
        )

    def test_default_config_has_stt_provider_and_model_profile(self) -> None:
        config = DEFAULT_CONFIG

        self.assertEqual(config["stt"]["provider"], "faster_whisper")
        self.assertIn(config["stt"]["whisper_model_size"], {"small", "medium"})
        self.assertIn(
            config["stt"]["whisper_model_profile"],
            {"balanced_small", "accuracy_medium"},
        )

    def test_default_config_has_dormant_sensevoice_defaults(self) -> None:
        config = DEFAULT_CONFIG

        self.assertEqual(config["stt"]["provider"], "faster_whisper")
        self.assertEqual(config["stt"]["sensevoice_model"], "SenseVoiceSmall")
        self.assertEqual(config["stt"]["sensevoice_device"], "cpu")
        self.assertEqual(config["stt"]["sensevoice_language"], "zh")

    def test_user_config_can_override_stt_provider_without_changing_defaults(self) -> None:
        config = load_config(CONFIG_PATH)

        self.assertIn(config["stt"]["provider"], {"faster_whisper", "funasr_sensevoice"})
        self.assertEqual(DEFAULT_CONFIG["stt"]["provider"], "faster_whisper")
        self.assertEqual(DEFAULT_CONFIG["stt"]["sensevoice_device"], "cpu")
        self.assertEqual(settings.SENSEVOICE_MODEL, "SenseVoiceSmall")
        self.assertIn(settings.SENSEVOICE_DEVICE, {"cpu", "cuda"})
        self.assertEqual(settings.SENSEVOICE_LANGUAGE, "zh")

    def test_stt_model_profiles_resolve_to_whisper_model_sizes(self) -> None:
        self.assertEqual(settings.resolve_whisper_model_profile("balanced_small"), "small")
        self.assertEqual(settings.resolve_whisper_model_profile("accuracy_medium"), "medium")
        self.assertEqual(
            settings.WHISPER_MODEL_SIZE,
            settings.resolve_whisper_model_profile(settings.WHISPER_MODEL_PROFILE),
        )

    def test_config_has_executor_launch_commands(self) -> None:
        config = load_config(CONFIG_PATH)

        self.assertIn(config["executor"]["default_target"], {"codex", "chatgpt", "cursor", "trae"})
        self.assertEqual(
            config["executor"]["codex_launch_command"],
            "explorer.exe shell:AppsFolder\\OpenAI.Codex_2p2nqsd0c76g0!App",
        )
        self.assertEqual(config["executor"]["codex_window_title"], "ChatGPT")
        self.assertEqual(config["executor"]["chatgpt_window_title"], "ChatGPT Classic")
        self.assertEqual(
            config["executor"]["chatgpt_launch_command"],
            "explorer.exe shell:AppsFolder\\OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0!ChatGPT",
        )
        self.assertEqual(config["executor"]["chatgpt_launch_timeout"], 15.0)
        self.assertEqual(config["executor"]["chatgpt_launch_poll_interval"], 0.5)
        self.assertEqual(config["executor"]["cursor_window_title"], "Cursor")
        self.assertEqual(config["executor"]["cursor_launch_command"], "explorer.exe shell:AppsFolder\\Anysphere.Cursor")
        self.assertEqual(config["executor"]["cursor_launch_timeout"], 15.0)
        self.assertEqual(config["executor"]["cursor_launch_poll_interval"], 0.5)
        self.assertNotIn("cursor_composer_click_rel_x", config["executor"])
        self.assertNotIn("cursor_composer_click_rel_y", config["executor"])
        self.assertEqual(config["executor"]["trae_launch_command"], "explorer.exe shell:AppsFolder\\ByteDance.TraeCN")
        self.assertNotIn("trae_composer_click_rel_x", config["executor"])
        self.assertNotIn("trae_composer_click_rel_y", config["executor"])
        self.assertNotIn("trae_focus_strategy", config["executor"])
        self.assertEqual(config["executor"]["trae_neutral_click_rel_x"], 0.5)
        self.assertEqual(config["executor"]["trae_neutral_click_rel_y"], 0.98)
        self.assertEqual(config["executor"]["trae_ai_sidebar_shortcut"], "ctrl+u")

    def test_runtime_files_are_grouped_by_purpose_under_logs(self) -> None:
        self.assertEqual(settings.LOG_DIR.name, "logs")
        self.assertEqual(settings.TRAY_LOG_DIR, settings.LOG_DIR / "tray")
        self.assertEqual(settings.HISTORY_DIR, settings.LOG_DIR / "history")
        self.assertEqual(settings.DIAGNOSTICS_DIR, settings.LOG_DIR / "diagnostics")
        self.assertEqual(settings.RUNTIME_DIR, settings.LOG_DIR / "runtime")

        self.assertEqual(settings.log_file_path().parent, settings.TRAY_LOG_DIR)
        self.assertEqual(settings.COMMAND_HISTORY_PATH, settings.HISTORY_DIR / "command_history.jsonl")
        self.assertEqual(settings.DIAGNOSTICS_HISTORY_PATH, settings.DIAGNOSTICS_DIR / "diagnostics.jsonl")
        self.assertEqual(settings.RUNTIME_STATUS_PATH, settings.RUNTIME_DIR / "runtime_status.json")
        self.assertEqual(CONTROL_COMMAND_PATH, settings.RUNTIME_DIR / "control_command.json")
        self.assertEqual(CONTROL_RESPONSE_PATH, settings.RUNTIME_DIR / "control_response.json")


if __name__ == "__main__":
    unittest.main()
