"""Central configuration for VoiceControl.

All tunable parameters and paths live here. No hardcoded paths or magic
numbers should appear elsewhere in the codebase.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from voicecontrol.config.manager import load_config

# --- Paths -----------------------------------------------------------------
# Project root = three levels up from this file (src/voicecontrol/config/settings.py).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]

AUDIO_FILES_DIR: Path = PROJECT_ROOT / "audio_files"
RECORDINGS_DIR: Path = AUDIO_FILES_DIR / "recordings"
TEMP_DIR: Path = AUDIO_FILES_DIR / "temp"
SAMPLES_DIR: Path = AUDIO_FILES_DIR / "samples"

# Default WAV for manual/debug single-shot scripts (``__main__`` blocks).
DEFAULT_RECORDING_PATH: Path = RECORDINGS_DIR / "test.wav"

# --- Audio capture ---------------------------------------------------------
SAMPLE_RATE: int = 16000
CHANNELS: int = 1
DTYPE: str = "float32"
DEFAULT_RECORD_SECONDS: int = 5
# None = use the system default input device; otherwise a sounddevice index.
INPUT_DEVICE: int | None = None

# --- Hotkeys ---------------------------------------------------------------
# Press RECORD_HOTKEY once to start recording, again to stop. QUIT_HOTKEY exits.
RECORD_HOTKEY: str = "f9"
QUIT_HOTKEY: str = "esc"

# --- VAD auto-stop ---------------------------------------------------------
# Speech probability (0-1) above which a frame counts as speech.
VAD_SPEECH_THRESHOLD: float = 0.5
# Stop after this much trailing silence once speech has been detected (s).
VAD_SILENCE_DURATION: float = 3.0
# Minimum total speech before auto-stop may trigger (s) — avoids early cutoff.
VAD_MIN_SPEECH_DURATION: float = 0.3
# Safety caps for the auto-stop capture loop.
VAD_MAX_RECORD_SECONDS: float | None = 180.0  # None disables the hard cap.
VAD_START_TIMEOUT: float = 8.0         # give up if no speech starts at all
VAD_POLL_INTERVAL: float = 0.15        # how often to re-check the buffer (s)

# --- Speech-to-text (faster-whisper) ---------------------------------------
WHISPER_MODEL_SIZE: str = "small"          # upgrade path: medium -> large-v3
WHISPER_DEVICE: str = "cuda"               # fallback "cpu"
WHISPER_COMPUTE_TYPE: str = "float16"      # fallback "int8"
# Chinese-primary, English also expected; None lets Whisper auto-detect.
WHISPER_LANGUAGE: str | None = None
WHISPER_BEAM_SIZE: int = 5
# Drop non-speech segments before decoding — kills silence/noise hallucinations.
WHISPER_VAD_FILTER: bool = True
# Don't feed prior text back in — avoids repetition/hallucination loops.
WHISPER_CONDITION_ON_PREVIOUS_TEXT: bool = False

# CPU fallback values, applied when CUDA is unavailable.
WHISPER_CPU_DEVICE: str = "cpu"
WHISPER_CPU_COMPUTE_TYPE: str = "int8"

# --- Executor / desktop automation -----------------------------------------
# Substring (case-insensitive) used to locate the target app window.
DEFAULT_EXECUTOR_TARGET: str = "codex"
CODEX_WINDOW_TITLE: str = "Codex"
# Optional executable path or launch command used when the Codex window is absent.
CODEX_LAUNCH_COMMAND: str = ""
CODEX_LAUNCH_TIMEOUT: float = 15.0
CODEX_LAUNCH_POLL_INTERVAL: float = 0.5
CHATGPT_WINDOW_TITLE: str = "ChatGPT"
CHATGPT_LAUNCH_COMMAND: str = ""
CHATGPT_LAUNCH_TIMEOUT: float = 15.0
CHATGPT_LAUNCH_POLL_INTERVAL: float = 0.5
CURSOR_WINDOW_TITLE: str = "Cursor"
CURSOR_LAUNCH_COMMAND: str = "explorer.exe shell:AppsFolder\\Anysphere.Cursor"
CURSOR_LAUNCH_TIMEOUT: float = 15.0
CURSOR_LAUNCH_POLL_INTERVAL: float = 0.5
# Press Enter after pasting to submit the prompt.
SEND_PROMPT_AUTO_ENTER: bool = True
# Delays (seconds) around desktop actions — keep small but non-zero (AGENTS §6).
FOCUS_SETTLE_DELAY: float = 0.3
PASTE_DELAY: float = 0.15
ENTER_DELAY: float = 0.1

# Focusing the window alone does not put the caret in the composer, so we
# click the input box first. Coordinates are relative to the window rect
# (0.0-1.0). Default targets the bottom-center composer of an active chat.
CLICK_COMPOSER_BEFORE_PASTE: bool = True
COMPOSER_CLICK_REL_X: float = 0.5
COMPOSER_CLICK_REL_Y: float = 0.9
CLICK_SETTLE_DELAY: float = 0.15

# --- Wake word -------------------------------------------------------------
# openWakeWord pretrained model name; "hey_jarvis" gates activation (English
# wake word, but the command you speak afterwards can still be Chinese).
WAKE_WORD_MODEL: str = "hey_jarvis"
WAKE_THRESHOLD: float = 0.5
WAKE_FRAME_SAMPLES: int = 1280          # 80 ms @ 16 kHz — openWakeWord frame
WAKE_INFERENCE_FRAMEWORK: str = "onnx"  # reuse installed onnxruntime
WAKE_COOLDOWN: float = 2.0              # ignore re-triggers within this window (s)

# --- Feedback cues ---------------------------------------------------------
# Audible beeps so you know it heard the wake word / finished (no GUI needed).
FEEDBACK_ENABLED: bool = True
FEEDBACK_WAKE_FREQ: int = 880
FEEDBACK_WAKE_MS: int = 150
FEEDBACK_DONE_FREQ: int = 1320
FEEDBACK_DONE_MS: int = 120

# --- Text-to-speech --------------------------------------------------------
TTS_ENABLED: bool = True
TTS_RATE: int = 0
TTS_VOLUME: int = 100
TTS_VOICE: str | None = None

# --- Desktop pet -----------------------------------------------------------
DESKTOP_PET_ANIMATION_ENABLED: bool = True

# --- Logging / tray daemon -------------------------------------------------
# Background (tray) mode: one log file per day under TRAY_LOG_DIR (pythonw has no console).
# Foreground CLI (main.py) logs to the console only; it does not use log_file_path().
LOG_DIR: Path = PROJECT_ROOT / "logs"
TRAY_LOG_DIR: Path = LOG_DIR / "tray"
HISTORY_DIR: Path = LOG_DIR / "history"
DIAGNOSTICS_DIR: Path = LOG_DIR / "diagnostics"
RUNTIME_DIR: Path = LOG_DIR / "runtime"
COMMAND_HISTORY_PATH: Path = HISTORY_DIR / "command_history.jsonl"
DIAGNOSTICS_HISTORY_PATH: Path = DIAGNOSTICS_DIR / "diagnostics.jsonl"
RUNTIME_STATUS_PATH: Path = RUNTIME_DIR / "runtime_status.json"
DESKTOP_PET_STATE_PATH: Path = RUNTIME_DIR / "desktop_pet_state.json"


def log_file_path() -> Path:
    """Return today's log file path (one file per calendar day, append on restart)."""
    day = datetime.now().strftime("%Y%m%d")
    return TRAY_LOG_DIR / f"{day}_voicecontrol.log"

# --- Autostart -------------------------------------------------------------
# Registry value name under HKCU...\Run used to toggle launch-at-logon.
AUTOSTART_APP_NAME: str = "VoiceControl"


_USER_CONFIG = load_config(PROJECT_ROOT / "config.json")

_AUDIO_CONFIG = _USER_CONFIG["audio"]
INPUT_DEVICE = _AUDIO_CONFIG["input_device"]

_HOTKEY_CONFIG = _USER_CONFIG["hotkeys"]
RECORD_HOTKEY = _HOTKEY_CONFIG["record_hotkey"]
QUIT_HOTKEY = _HOTKEY_CONFIG["quit_hotkey"]

_VAD_CONFIG = _USER_CONFIG["vad"]
VAD_SPEECH_THRESHOLD = _VAD_CONFIG["speech_threshold"]
VAD_SILENCE_DURATION = _VAD_CONFIG["silence_duration"]
VAD_MIN_SPEECH_DURATION = _VAD_CONFIG["min_speech_duration"]
VAD_MAX_RECORD_SECONDS = _VAD_CONFIG["max_record_seconds"]
VAD_START_TIMEOUT = _VAD_CONFIG["start_timeout"]
VAD_POLL_INTERVAL = _VAD_CONFIG["poll_interval"]

_STT_CONFIG = _USER_CONFIG["stt"]
WHISPER_MODEL_SIZE = _STT_CONFIG["whisper_model_size"]
WHISPER_DEVICE = _STT_CONFIG["whisper_device"]
WHISPER_COMPUTE_TYPE = _STT_CONFIG["whisper_compute_type"]
WHISPER_LANGUAGE = _STT_CONFIG["whisper_language"]
WHISPER_BEAM_SIZE = _STT_CONFIG["whisper_beam_size"]
WHISPER_VAD_FILTER = _STT_CONFIG["whisper_vad_filter"]
WHISPER_CONDITION_ON_PREVIOUS_TEXT = _STT_CONFIG["whisper_condition_on_previous_text"]

_EXECUTOR_CONFIG = _USER_CONFIG["executor"]
DEFAULT_EXECUTOR_TARGET = _EXECUTOR_CONFIG["default_target"]
CODEX_WINDOW_TITLE = _EXECUTOR_CONFIG["codex_window_title"]
CODEX_LAUNCH_COMMAND = _EXECUTOR_CONFIG["codex_launch_command"]
CODEX_LAUNCH_TIMEOUT = _EXECUTOR_CONFIG["codex_launch_timeout"]
CODEX_LAUNCH_POLL_INTERVAL = _EXECUTOR_CONFIG["codex_launch_poll_interval"]
CHATGPT_WINDOW_TITLE = _EXECUTOR_CONFIG["chatgpt_window_title"]
CHATGPT_LAUNCH_COMMAND = _EXECUTOR_CONFIG["chatgpt_launch_command"]
CHATGPT_LAUNCH_TIMEOUT = _EXECUTOR_CONFIG["chatgpt_launch_timeout"]
CHATGPT_LAUNCH_POLL_INTERVAL = _EXECUTOR_CONFIG["chatgpt_launch_poll_interval"]
CURSOR_WINDOW_TITLE = _EXECUTOR_CONFIG["cursor_window_title"]
CURSOR_LAUNCH_COMMAND = _EXECUTOR_CONFIG["cursor_launch_command"]
CURSOR_LAUNCH_TIMEOUT = _EXECUTOR_CONFIG["cursor_launch_timeout"]
CURSOR_LAUNCH_POLL_INTERVAL = _EXECUTOR_CONFIG["cursor_launch_poll_interval"]
SEND_PROMPT_AUTO_ENTER = _EXECUTOR_CONFIG["send_prompt_auto_enter"]
CLICK_COMPOSER_BEFORE_PASTE = _EXECUTOR_CONFIG["click_composer_before_paste"]
COMPOSER_CLICK_REL_X = _EXECUTOR_CONFIG["composer_click_rel_x"]
COMPOSER_CLICK_REL_Y = _EXECUTOR_CONFIG["composer_click_rel_y"]

_WAKE_WORD_CONFIG = _USER_CONFIG["wake_word"]
WAKE_WORD_MODEL = _WAKE_WORD_CONFIG["model"]
WAKE_THRESHOLD = _WAKE_WORD_CONFIG["threshold"]
WAKE_COOLDOWN = _WAKE_WORD_CONFIG["cooldown"]

_FEEDBACK_CONFIG = _USER_CONFIG["feedback"]
FEEDBACK_ENABLED = _FEEDBACK_CONFIG["enabled"]
FEEDBACK_WAKE_FREQ = _FEEDBACK_CONFIG["wake_freq"]
FEEDBACK_WAKE_MS = _FEEDBACK_CONFIG["wake_ms"]
FEEDBACK_DONE_FREQ = _FEEDBACK_CONFIG["done_freq"]
FEEDBACK_DONE_MS = _FEEDBACK_CONFIG["done_ms"]

_TTS_CONFIG = _USER_CONFIG["tts"]
TTS_ENABLED = _TTS_CONFIG["enabled"]
TTS_RATE = _TTS_CONFIG["rate"]
TTS_VOLUME = _TTS_CONFIG["volume"]
TTS_VOICE = _TTS_CONFIG["voice"]

_DESKTOP_PET_CONFIG = _USER_CONFIG["desktop_pet"]
DESKTOP_PET_ANIMATION_ENABLED = _DESKTOP_PET_CONFIG["animation_enabled"]


def ensure_dirs() -> None:
    """Create the audio working directories if they don't exist yet."""
    for directory in (RECORDINGS_DIR, TEMP_DIR, SAMPLES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def new_recording_path(prefix: str = "command") -> Path:
    """Return a fresh timestamped WAV path under ``RECORDINGS_DIR``.

    Used by the live pipeline so each utterance is kept (instead of
    overwriting a single ``test.wav``), aiding later debugging.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return RECORDINGS_DIR / f"{prefix}_{timestamp}.wav"


if __name__ == "__main__":
    ensure_dirs()
    print(f"PROJECT_ROOT          = {PROJECT_ROOT}")
    print(f"RECORDINGS_DIR        = {RECORDINGS_DIR}")
    print(f"DEFAULT_RECORDING_PATH= {DEFAULT_RECORDING_PATH}")
    print(f"SAMPLE_RATE           = {SAMPLE_RATE}")
    print(f"CHANNELS              = {CHANNELS}")
    print(f"DEFAULT_RECORD_SECONDS= {DEFAULT_RECORD_SECONDS}")
    print(f"WHISPER_MODEL_SIZE    = {WHISPER_MODEL_SIZE}")
    print(f"WHISPER_DEVICE        = {WHISPER_DEVICE} ({WHISPER_COMPUTE_TYPE})")
