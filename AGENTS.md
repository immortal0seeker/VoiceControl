# AGENTS.md — VoiceControl

Voice-driven AI desktop assistant for Windows 11. Local Python project; **MVP shipped**, with ongoing post-MVP features (settings UI, TTS status cues, diagnostics, command history).

End-to-end goal:

```text
speak → wake word → record → speech-to-text → route command
      → send to Codex / ChatGPT / Cursor → execute task → optional TTS
```

This is a **local desktop automation system driven by voice**, not a generic chatbot.

---

## 1. Environment

```text
OS         Windows 11
Python     3.11+  (.venv only — never use global Python)
GPU        NVIDIA CUDA recommended (8 GB+ VRAM for small/medium Whisper)
           CPU fallback supported (int8)
Shell      PowerShell  (use ';' to chain commands, NOT '&&')
```

Install inside `.venv`:

```powershell
pip install -r requirements.txt
pip install -e .
```

The editable install registers the `voicecontrol` package so
`python -m voicecontrol.*` works from any directory.

---

## 2. Project Decisions (do not re-ask)

| Topic | Decision |
|-------|----------|
| STT engine | `faster-whisper` |
| Languages | Chinese-primary + English (multilingual model) |
| Default model | `small` (upgrade path: `medium` → `large-v3`) |
| Compute | GPU first: `device="cuda"`, `compute_type="float16"`; CPU fallback (`int8`) |
| User config | Root `config.json` merged over code defaults via `config/manager.py`; `settings.py` re-exports merged values |
| Executor targets (in order) | Codex Desktop → ChatGPT Desktop → Cursor → others (only Codex implemented) |
| Executor design | Pluggable `AppDriver` interface, one driver per target app |
| VAD engine | Silero VAD ONNX bundled with faster-whisper (via onnxruntime, no torch) |
| Wake word engine | openWakeWord (ONNX/onnxruntime); built-in `hey_jarvis` or bundled custom `world_activate.onnx` — wake word only gates activation; commands stay Chinese |
| TTS | Windows SAPI via `pywin32` (`tts/speaker.py`); short **status phrases** on pipeline events (not full read-back of Codex replies) |
| Background mode | Tray app via `pythonw`, launch-at-logon through HKCU Run key. NOT a Windows Service (session 0 cannot drive the desktop) |
| Inter-process control | File-based commands in `logs/control_command.json` (start/stop recording, pause/resume listening) consumed by tray daemon |

---

## 3. Shipped Features

```text
Single-shot recording       python -m voicecontrol.main --once
Hotkey trigger              F9 start/stop (default loop), Esc quit
VAD auto-stop               --vad flag on hotkey loop
Wake word + tray daemon     --wake (foreground) or pythonw -m voicecontrol.tray_app
Codex Desktop executor      focus → click composer → paste → Enter; optional auto-launch
Settings UI (PySide6)       python -m voicecontrol.ui.settings_app  (also from tray menu)
Launch at logon             tray menu toggle (HKCU Run)
TTS status cues             "我在" / "请说" / "正在识别" / … on pipeline status events
Command history             append-only JSONL under logs/command_history.jsonl
Diagnostics                 mic / VAD / wake-word tests in settings UI
Manual recording            tray menu or settings UI → file control command → skip wake word
Custom wake word            bundled world_activate.onnx selectable in config.json / settings UI
```

Typical production flow:

```text
always-on tray daemon → openWakeWord hears wake word → beep cue (+ optional TTS "我在")
→ record command (VAD auto-stop; F9 or tray can stop early)
→ transcribe → send to Codex → history + done cue (+ optional TTS "已发送")
tray menu: pause/resume · start/stop recording · open settings · toggle launch-at-logon · quit
```

Run commands (PowerShell):

```powershell
.venv\Scripts\python.exe -m voicecontrol.main --wake          # foreground debug
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app             # headless tray daemon
.venv\Scripts\python.exe -m voicecontrol.ui.settings_app      # settings / diagnostics UI
```

Logs (tray mode): `logs/YYYYMMDD_voicecontrol.log` (one file per calendar day).

---

## 4. Repository Structure

Create files lazily — do not scaffold empty modules ahead of need.

Packaged as a src-layout `voicecontrol` package (importable after
`pip install -e .`); always use absolute `voicecontrol.*` imports, never `src.*`.

```text
VoiceControl/
├── .venv/
├── config.json                 user-facing JSON config (merged over defaults)
├── audio_files/                recordings/  temp/  samples/   (debug audio, git-ignored)
├── logs/                       daily tray logs, command_history.jsonl, diagnostics.jsonl,
│                               control_command.json (git-ignored)
├── pyproject.toml              package definition (src-layout, console script, package-data)
├── src/voicecontrol/
│   ├── main.py                 CLI entry: --once / --vad / --wake / --no-send
│   ├── tray_app.py             headless system-tray daemon
│   ├── audio/                  device_manager, recorder (StreamRecorder, MicFrameStream)
│   ├── stt/                    whisper_engine
│   ├── wake_word/              detector, models.py, models/*.onnx
│   ├── vad/                    silero_vad (incremental endpointing)
│   ├── executor/               app_driver (base), codex_driver, window_utils
│   ├── pipeline/               orchestrator (VoiceOrchestrator, run_wake_loop)
│   ├── config/                 settings.py, manager.py
│   ├── control/                file-based commands for tray daemon
│   ├── events/                 status publisher (pipeline → tray / TTS / UI)
│   ├── history/                command history store + resend
│   ├── diagnostics/            mic / VAD / wake-word tests, log reader, diagnostic result store
│   ├── tts/                    Windows SAPI speaker + status speech subscriber
│   ├── ui/                     PySide6 settings/diagnostics UI
│   │   ├── settings_app.py     QApplication entry point
│   │   ├── settings_window.py  navigation shell (sidebar + QStackedWidget)
│   │   ├── config_binding.py   config read/write helpers + Binding type
│   │   ├── style.py            Apple-style QSS stylesheet
│   │   ├── widgets.py          reusable form widgets (card, switch, combo, …)
│   │   ├── assets.py           asset path resolver
│   │   └── pages/              one QWidget subclass per page
│   │       ├── base.py         page_layout scaffold + PlaceholderPage
│   │       ├── status_page.py
│   │       ├── recording_page.py
│   │       ├── settings_page.py
│   │       ├── diagnostics_page.py
│   │       ├── command_history_page.py
│   │       ├── logs_page.py
│   │       └── background_page.py
│   └── utils/                  feedback (beeps), autostart, hotkeys
├── requirements.txt
├── README.md
├── README_EN.md
├── AGENTS.md
└── AGENTS_CN.md
```

Module boundaries (keep responsibilities separate):

- `audio/` — list devices, record, save/play WAV, validate. No STT/VAD/wake-word logic.
- `stt/` — load model, transcribe file, normalize result. No mic logic.
- `executor/` — focus window, send text, simulate input. No STT/recording logic.
- `pipeline/` — orchestrate the slices; call lower modules, don't reimplement them.
- `config/` — defaults in `settings.py`; user overrides in `config.json` via `manager.py`.
- `control/` — file-based IPC commands consumed by the tray daemon.
- `events/` — in-process status pub/sub shared by pipeline, tray, TTS, settings UI.
- `history/` — append-only command history; resend last command from settings UI.
- `diagnostics/` — self-test helpers surfaced in the settings UI.
- `tts/` — Windows SAPI wrapper and status-phrase subscriber only.
- `ui/` — PySide6 settings/diagnostics window; no pipeline logic.
- `utils/` — only code that fits nowhere else.

---

## 5. Key Defaults (config)

Code defaults live in `settings.py`; runtime values come from merged `config.json`.
Edit via settings UI or hand-edit `config.json`, then **restart tray/listener**.

```python
SAMPLE_RATE = 16000
CHANNELS = 1
WHISPER_MODEL_SIZE = "small"
WHISPER_DEVICE = "cuda"          # fallback "cpu"
WHISPER_COMPUTE_TYPE = "float16" # fallback "int8"
VAD_SILENCE_DURATION = 3.0
WAKE_WORD_MODEL = "hey_jarvis"   # or bundled "world_activate"
WAKE_THRESHOLD = 0.5
CODEX_WINDOW_TITLE = "Codex"
CODEX_LAUNCH_COMMAND = ""        # optional; launch Codex if window missing
TTS_ENABLED = True               # status phrases via Windows SAPI
RECORD_HOTKEY = "f9"             # also manual stop during wake-loop recording
```

STT module must support at least:

```python
def transcribe_file(path: str | Path) -> str: ...
# later: def transcribe_array(audio: np.ndarray, sample_rate: int) -> str: ...
```

---

## 6. Executor Design

Multiple target apps are planned, so use a thin driver abstraction (this is a justified abstraction, not premature).

```python
class AppDriver:
    """One driver per target app (Codex, ChatGPT, Cursor, ...)."""
    def focus(self) -> None: ...
    def send_prompt(self, text: str) -> None: ...   # prefer clipboard paste + Enter
```

`CodexDriver` additionally supports `CODEX_LAUNCH_COMMAND`: if the window is missing, run the configured command and poll until the title appears.

Rules:

- Implement Codex Desktop first; add others as drivers later.
- Prefer **clipboard paste** over char-by-char typing (Chinese / long prompts).
- Add small delays and clear logs around every desktop action.
- Watch out for: Alt+Tab instability, IME issues, focus loss, admin-permission boundaries, hotkeys captured by the editor.

Tools when needed: `pyperclip`, `pywin32`, `keyboard`.

---

## 7. Coding Rules

- Simple, readable Python; small functions; explicit over clever.
- Type hints on public functions/methods where practical.
- `pathlib.Path` for paths. No hardcoded paths outside `config/`.
- `logging` in reusable modules; `print` only in CLI entry points and `__main__` debug blocks.
- Naming: `snake_case` files/funcs/vars/modules, `PascalCase` classes, `UPPER_CASE` constants.
- Avoid global mutable state unless clearly required.

---

## 8. Error Handling

Handle Windows failures explicitly — never silently swallow:

```text
mic unavailable · invalid device index · audio file missing
model load failure · empty transcription · window not found
permission denied · hotkey conflict · TTS/SAPI unavailable
```

Reusable modules: raise clear exceptions or log. CLI entry points: printing the error is fine.

Audio rules: always allow manual testing; save debug WAVs early; handle missing mics gracefully; never assume the default device is correct; provide a device-listing function.

---

## 9. Dependencies

All runtime deps are in `requirements.txt` and mirrored in `pyproject.toml`.
Add intentionally: explain why, prefer stable/common packages, no duplicates.

Bundled package data (via `pyproject.toml`): `ui/assets/*`, `wake_word/models/*`.

---

## 10. Out of Scope (for now)

```text
Full conversational TTS (reading Codex replies aloud)
Obsidian · Computer Use · LLM router · multi-agent
Packaged installer
true Windows Service (session 0 can't drive the desktop — use the tray app)
ChatGPT/Cursor drivers (planned as new AppDriver subclasses)
transcribe_array (in-memory STT without temp WAV)
```

---

## 11. Agent Behavior

1. Read `README.md` and this file first; inspect the file tree before creating files.
2. Make the smallest useful change; keep code runnable at every step.
3. One working vertical slice beats many half-finished modules.
4. Preserve naming conventions; don't rewrite unrelated files.
5. State the exact PowerShell commands the user should run.
6. For uncertain Windows audio behavior, write a diagnostic script first.

Philosophy: **make it run → make it observable → make it stable → make it fast → make it intelligent.**
