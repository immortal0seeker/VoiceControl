# AGENTS.md - VoiceControl

VoiceControl is a local Windows 11 voice-driven desktop automation assistant. The MVP has shipped, and the current post-MVP work focuses on multi-target executors, settings UI, status TTS cues, diagnostics, command history, and desktop-pet UX.

End-to-end goal:

```text
speak -> wake word -> record -> speech-to-text -> route command
      -> send to Codex / ChatGPT / Cursor / Trae -> execute task -> optional TTS
```

This is a local desktop automation system driven by voice, not a generic chatbot.

---

## 1. Environment

```text
OS         Windows 11
Python     3.11+  (.venv only; never use global Python)
GPU        NVIDIA CUDA recommended; CPU int8 fallback supported
Shell      PowerShell  (use ';' to chain commands, not '&&')
```

Install inside `.venv`:

```powershell
pip install -r requirements.txt
pip install -e .
```

The editable install registers the `voicecontrol` package so `python -m voicecontrol.*` works from any directory.

---

## 2. Project Decisions

| Topic | Decision |
| --- | --- |
| STT engine | Provider factory via `create_stt_engine()`; default `faster_whisper`, optional `funasr_sensevoice` |
| Languages | Chinese-primary + English, using a multilingual model |
| Default STT model | Whisper `small`; optional choices: Whisper `medium`, SenseVoice-Small |
| Compute | GPU first: `device="cuda"`, `compute_type="float16"`; CPU fallback: `int8` |
| User config | Root `config.json` merged over defaults via `config/manager.py`; `settings.py` exports merged values |
| Executor targets | Codex Desktop, ChatGPT Desktop, Cursor, Trae |
| Executor design | Pluggable `AppDriver`; reusable `LaunchableAppDriver`; `executor/router.py` selects the configured target |
| VAD engine | Silero VAD ONNX bundled through faster-whisper / onnxruntime, no torch |
| Wake word engine | openWakeWord ONNX; built-in `hey_jarvis` or bundled custom `world_activate.onnx` |
| TTS | Windows SAPI via `pywin32`; short status phrases only, not full reply read-back |
| Background mode | Tray app via `pythonw`; launch-at-logon via HKCU Run key; not a Windows Service |
| Inter-process control | File commands in `logs/runtime/control_command.json`, with acknowledgements in `logs/runtime/control_response.json` |

---

## 3. Shipped Features

```text
Debug CLI recording         python -m voicecontrol.main --once
Debug CLI hotkey trigger    F9 start/stop, Esc quit
VAD auto-stop               --vad flag on hotkey loop
Wake word + tray daemon     --wake or pythonw -m voicecontrol.tray_app
Executor routing            codex / chatgpt / cursor / trae selected by executor.default_target
Codex driver                focus -> click composer -> paste -> Enter; optional auto-launch
ChatGPT driver              focus -> Ctrl+Shift+L -> paste -> Enter; optional auto-launch
Cursor driver               focus -> Ctrl+Shift+L -> paste -> Enter; optional auto-launch
Trae driver                 focus -> bottom neutral click -> Ctrl+U -> paste -> Enter; optional auto-launch
Control center              python -m voicecontrol.ui.settings_app
Desktop pet                 pythonw -m voicecontrol.ui.desktop_pet_app
Launch at logon             tray menu toggle
TTS status cues             short pipeline event phrases
Runtime status              logs/runtime/runtime_status.json
Command history             logs/history/command_history.jsonl
Diagnostics                 mic / VAD / wake-word / STT model compare / TTS / target-send tests
Manual recording            tray/settings control command, bypassing wake word
Custom wake word            bundled world_activate.onnx
```

Typical production flow:

```text
tray daemon -> wake word -> beep/TTS cue -> record command -> transcribe
-> route to configured AppDriver -> paste/send -> history + done cue
```

Run commands:

```powershell
.venv\Scripts\python.exe -m voicecontrol.main --wake
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app
.venv\Scripts\python.exe -m voicecontrol.ui.settings_app
.venv\Scripts\pythonw.exe -m voicecontrol.ui.desktop_pet_app
```

Logs in tray mode: `logs/tray/YYYYMMDD_voicecontrol.log`.

---

## 4. Repository Structure

Create files lazily. Do not scaffold empty modules ahead of need.

Always use absolute `voicecontrol.*` imports, never `src.*`.

```text
VoiceControl/
├── config.json
├── audio_files/                 recordings/, temp/, samples/ (git-ignored)
├── logs/                        tray/, history/, diagnostics/, runtime/ (git-ignored)
├── pyproject.toml
├── requirements.txt
├── README.md
├── README_EN.md
├── AGENTS.md
├── AGENTS_CN.md
└── src/voicecontrol/
    ├── main.py
    ├── tray_app.py
    ├── audio/
    ├── stt/                 STTEngine protocol, WhisperEngine, SenseVoiceEngine, provider factory
    ├── vad/
    ├── wake_word/
    ├── executor/
    │   ├── app_driver.py        AppDriver + LaunchableAppDriver
    │   ├── router.py            create_driver / get_default_driver
    │   ├── codex_driver.py
    │   ├── chatgpt_driver.py
    │   ├── cursor_driver.py
    │   ├── trae_driver.py
    │   └── window_utils.py
    ├── pipeline/
    ├── config/
    ├── control/
    ├── events/
    ├── history/
    ├── diagnostics/
    ├── tts/
    ├── ui/
    └── utils/
```

Module boundaries:

- `audio/` lists devices, records, saves/plays WAV, and validates audio. No STT/VAD/wake-word logic.
- `stt/` loads Whisper and transcribes files. No microphone logic.
- `executor/` focuses target windows and sends text. No STT/recording logic.
- `pipeline/` orchestrates lower modules and depends on `AppDriver`, not concrete drivers.
- `config/` owns defaults and user override merging.
- `control/` owns file-based tray IPC commands.
- `events/` owns in-process status pub/sub and runtime status snapshots.
- `history/` owns append-only command history and resend.
- `diagnostics/` owns self-tests surfaced in the UI.
- `tts/` owns Windows SAPI status speech only.
- `ui/` owns PySide6 control center and desktop pet. No pipeline logic.
- `utils/` contains only cross-cutting helpers that fit nowhere else.

---

## 5. Key Config Defaults

Runtime values come from merged `config.json`. After editing config, restart tray/listener.

```python
SAMPLE_RATE = 16000
CHANNELS = 1
WHISPER_MODEL_SIZE = "small"
STT_PROVIDER = "faster_whisper"  # faster_whisper | funasr_sensevoice
SENSEVOICE_MODEL = "SenseVoiceSmall"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE_TYPE = "float16"
VAD_SILENCE_DURATION = 3.0
WAKE_WORD_MODEL = "hey_jarvis"
WAKE_THRESHOLD = 0.5
DEFAULT_EXECUTOR_TARGET = "cursor"  # codex | chatgpt | cursor | trae
CODEX_WINDOW_TITLE = "Codex"
CHATGPT_WINDOW_TITLE = "ChatGPT"
CURSOR_WINDOW_TITLE = "Cursor"
TTS_ENABLED = True
RECORD_HOTKEY = "f9"
```

`config.json` currently includes AppsFolder launch commands for Codex, ChatGPT, Cursor, and Trae. Codex Desktop, ChatGPT Desktop, Cursor, and Trae have all been live-tested for opening, focusing/injecting text, and sending prompts.

STT defaults remain on `faster_whisper` + Whisper `small`. SenseVoice-Small support exists behind `stt.provider = "funasr_sensevoice"` and the settings UI, but the FunASR runtime is not part of the default project install yet. Missing SenseVoice dependencies should fail clearly in diagnostics instead of breaking Whisper comparison results.

---

## 6. Executor Design

Use the driver abstraction; do not hard-code target apps in pipeline/history/diagnostics.

```python
class AppDriver:
    app_name: str
    window_title: str
    def focus(self) -> Window: ...
    def send_prompt(self, text: str, auto_enter: bool | None = None) -> None: ...

class LaunchableAppDriver(AppDriver):
    launch_command: str
    launch_timeout: float
    launch_poll_interval: float
```

Rules:

- Route default target selection through `voicecontrol.executor.router.get_default_driver()`.
- Use `create_driver("codex" | "chatgpt" | "cursor" | "trae")` for explicit target creation.
- Prefer clipboard paste over character typing for Chinese and long prompts.
- ChatGPT Desktop and Cursor focus their composer with `Ctrl+Shift+L`.
- Trae first clicks the bottom neutral area to remove stale AI-sidebar focus, then uses `Ctrl+U` to focus the AI input. Do not click again after `Ctrl+U`.
- Codex still uses relative composer click coordinates.
- Keep desktop actions logged and delayed slightly.
- Be careful with focus loss, IME state, admin boundaries, and editor hotkeys.

---

## 7. Coding Rules

- Simple, readable Python; small functions; explicit over clever.
- Type hints on public functions and methods where practical.
- Use `pathlib.Path` for paths.
- Reusable modules use `logging`; `print` is fine only in CLI/debug entry points.
- Naming: `snake_case` for files/functions/vars/modules, `PascalCase` for classes, `UPPER_CASE` for constants.
- Avoid global mutable state unless clearly required.
- Preserve user changes in a dirty worktree; never revert unrelated edits.

---

## 8. Error Handling

Handle Windows failures explicitly. Never silently swallow:

```text
mic unavailable, invalid device index, missing audio file,
model load failure, empty transcription, window not found,
launch failure, permission denied, hotkey conflict, TTS/SAPI unavailable
```

Reusable modules should raise clear exceptions or log. CLI entry points may print user-facing errors.

---

## 9. Dependencies

Runtime dependencies live in `requirements.txt` and are mirrored in `pyproject.toml`. Add dependencies intentionally, explain why, prefer stable/common packages, and avoid duplicates.

Bundled package data:

```text
ui/assets/*
wake_word/models/*
```

---

## 10. Out of Scope For Now

```text
Full conversational TTS
LLM intent router
CLI-agent driver
Packaged installer
Automatic first-run app discovery
True Windows Service
transcribe_array
Bundling FunASR/SenseVoice runtime in default install
```

---

## 11. Agent Behavior

1. Read `README.md` and this file first; inspect the file tree before creating files.
2. Make the smallest useful change and keep the project runnable.
3. One working vertical slice beats many half-finished modules.
4. Preserve naming conventions; do not rewrite unrelated files.
5. State exact PowerShell commands the user should run.
6. For uncertain Windows audio behavior, write a diagnostic script first.

Philosophy: make it run -> make it observable -> make it stable -> make it fast -> make it intelligent.
