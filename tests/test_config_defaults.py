from __future__ import annotations

import unittest

from voicecontrol.config.manager import CONFIG_PATH, load_config
from voicecontrol.config import settings
from voicecontrol.control.commands import CONTROL_COMMAND_PATH, CONTROL_RESPONSE_PATH


class CheckedInConfigTests(unittest.TestCase):
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

    def test_checked_in_config_has_stt_provider_and_model_profile(self) -> None:
        config = load_config(CONFIG_PATH)

        self.assertEqual(config["stt"]["provider"], "faster_whisper")
        self.assertIn(config["stt"]["whisper_model_size"], {"small", "medium"})
        self.assertIn(
            config["stt"]["whisper_model_profile"],
            {"balanced_small", "accuracy_medium"},
        )
        self.assertEqual(settings.STT_PROVIDER, "faster_whisper")
        self.assertIn(settings.WHISPER_MODEL_PROFILE, {"balanced_small", "accuracy_medium"})

    def test_stt_model_profiles_resolve_to_whisper_model_sizes(self) -> None:
        self.assertEqual(settings.resolve_whisper_model_profile("balanced_small"), "small")
        self.assertEqual(settings.resolve_whisper_model_profile("accuracy_medium"), "medium")
        self.assertEqual(
            settings.WHISPER_MODEL_SIZE,
            settings.resolve_whisper_model_profile(settings.WHISPER_MODEL_PROFILE),
        )

    def test_checked_in_config_has_executor_launch_commands(self) -> None:
        config = load_config(CONFIG_PATH)

        self.assertEqual(config["executor"]["default_target"], "chatgpt")
        self.assertEqual(
            config["executor"]["codex_launch_command"],
            "explorer.exe shell:AppsFolder\\OpenAI.Codex_2p2nqsd0c76g0!App",
        )
        self.assertEqual(config["executor"]["chatgpt_window_title"], "ChatGPT")
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
        self.assertEqual(config["executor"]["cursor_composer_click_rel_x"], 0.83)
        self.assertEqual(config["executor"]["cursor_composer_click_rel_y"], 0.97)
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
