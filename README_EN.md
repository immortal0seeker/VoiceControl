<div align="right">

[中文](README.md) | **[English](README_EN.md)**

</div>

# VoiceControl

A local voice desktop assistant for Windows 11. Wake word → record → transcribe → send to Codex Desktop automatically.

```text
hey jarvis (or world_activate) → beep / TTS “我在” → speak command → auto-stop on silence → Whisper STT → paste into Codex
```

## Requirements

- Windows 11
- Python 3.11+ (use the project `.venv` only — do not use global Python)
- Microphone
- NVIDIA GPU optional (Whisper defaults to `cuda`/`float16`; falls back to CPU automatically)
- [Codex Desktop](https://openai.com/codex) should be running first (may be minimized; optional `codex_launch_command` in `config.json` can auto-launch it)

## Installation

```powershell
cd <project-directory>
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\pip.exe install -e .
```

`pip install -e .` installs the `voicecontrol` package in editable mode so `python -m voicecontrol.*` works from any directory.

The first run downloads Whisper and openWakeWord models; an internet connection is required. The bundled custom wake word `world_activate.onnx` ships with the package.

## Usage

### Settings UI

```powershell
.venv\Scripts\python.exe -m voicecontrol.ui.settings_app
```

You can also launch it from the tray menu (**Open settings**) or by double-clicking
the tray icon, in a separate process.

The UI reads and writes root `config.json`. **Restart the tray/listener** after saving.
The control center uses five sidebar pages: recording/status controls, settings
(including TTS), diagnostics, command history, and logs.

### Daily use (tray daemon, recommended)

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app
```

A **V** tray icon appears (loads `ui/assets/app_icon.png` when available). Right-click menu:

- Pause / resume listening
- Start / stop recording (skip wake word; record a command directly)
- Open settings
- Show / hide desktop pet
- Toggle launch-at-logon
- Quit

Double-clicking the tray icon opens the settings/control-center UI. Tray logs live
at `logs\tray\YYYYMMDD_voicecontrol.log` (one file per calendar day).

When TTS is enabled, short status phrases are spoken on pipeline events (e.g. “我在”, “请说”, “正在识别”, “已发送”).

### Desktop pet status window

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.ui.desktop_pet_app
```

The desktop pet is a minimal transparent always-on-top floating window. Drag it
to reposition it, left-click it to open the control center, or right-click it to
pause/resume listening, open the control center, or quit. It polls
`logs\runtime\runtime_status.json` every second and switches text expressions for
listening, recording, sending, and error states. It remembers its last position
on close. The Desktop Pet card in settings can disable the pulse animation.

### Foreground debug (console output)

`main.py` is now the developer/debug CLI. Daily use should prefer the tray
daemon.

```powershell
# Wake-word mode
.venv\Scripts\python.exe -m voicecontrol.main --wake

# Transcribe only; do not send to Codex
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
```

Say the wake word (default **“hey jarvis”** in English, or select **world_activate** in settings) → hear a beep / TTS → speak your command in Chinese → recording stops after ~3 s of silence; press **F9** during recording to stop early.

### Hotkey mode (no wake word)

```powershell
# Single fixed-duration recording (default 5 s)
.venv\Scripts\python.exe -m voicecontrol.main --once

# F9 start/stop, Esc quit
.venv\Scripts\python.exe -m voicecontrol.main

# F9 start; auto-stop when you finish speaking
.venv\Scripts\python.exe -m voicecontrol.main --vad
```

### Diagnostics

```powershell
# List microphone devices
.venv\Scripts\python.exe -m voicecontrol.audio.device_manager

# List visible windows (check Codex window title)
.venv\Scripts\python.exe -m voicecontrol.executor.window_utils

# Check autostart state and launch command
.venv\Scripts\python.exe -m voicecontrol.utils.autostart
```

The settings UI also offers mic, VAD, wake-word file, TTS, and Codex-send tests
plus recent log viewing.

## Configuration

User settings live in root [`config.json`](config.json), merged over code defaults by [`src/voicecontrol/config/manager.py`](src/voicecontrol/config/manager.py) and exported at runtime via [`settings.py`](src/voicecontrol/config/settings.py).

Common options:

| Parameter / config.json key | Default | Description |
| --- | --- | --- |
| `wake_word.model` | `hey_jarvis` | Wake word; bundled `world_activate` also available |
| `wake_word.threshold` | `0.5` | Wake sensitivity (lower = more sensitive) |
| `wake_word.cooldown` | `2.0` | Seconds to ignore re-triggers after a command finishes |
| `vad.silence_duration` | `3.0` | Trailing silence before stop (seconds) |
| `executor.codex_window_title` | `Codex` | Window title substring to match |
| `executor.codex_launch_command` | `""` | Shell command to launch Codex if the window is missing |
| `stt.whisper_model_size` | `small` | Upgrade path: `medium` / `large-v3` |
| `tts.enabled` | `true` | Windows SAPI short status phrases |
| `hotkeys.record_hotkey` | `f9` | Hotkey-mode record key; also manual stop during wake-loop recording |

## Project layout

```text
config.json
src/voicecontrol/
├── main.py           CLI entry (--once / --vad / --wake / --no-send)
├── tray_app.py       System-tray daemon
├── config/           settings.py, manager.py
├── audio/            Microphone & recording
├── stt/              faster-whisper
├── vad/              Silero VAD endpointing
├── wake_word/        openWakeWord + models/world_activate.onnx
├── executor/         Codex window focus + paste
├── pipeline/         Orchestration & status events
├── control/          Tray file commands (logs/runtime/control_command.json)
├── events/           Status pub/sub + runtime status snapshot
├── history/          Command history JSONL
├── diagnostics/      Self-test helpers
├── tts/              Windows SAPI status speech
├── ui/               PySide6 control center UI
│   ├── desktop_pet.py     Desktop pet floating window
│   └── desktop_pet_app.py Desktop pet entry point
└── utils/            Beeps, launch-at-logon, hotkeys
logs/
├── tray/             Daily tray logs (YYYYMMDD_voicecontrol.log)
├── history/          command_history.jsonl
├── diagnostics/      diagnostics.jsonl
└── runtime/          runtime_status.json, control_command.json
```

## Feature status

**Shipped**

- Microphone capture and faster-whisper transcription (Chinese / English)
- Hotkey trigger (F9 start/stop) and VAD auto-stop on silence
- Wake word (`hey_jarvis` / bundled `world_activate`) plus system-tray background daemon
- Tray manual recording, pause/resume, launch-at-logon toggle, and double-click settings
- Auto-focus Codex Desktop and paste commands; optional Codex auto-launch
- PySide6 control center backed by `config.json`
- Windows SAPI pipeline status TTS (short phrases)
- Runtime status snapshot (`logs/runtime/runtime_status.json`) polled by the recording page
- Command history (`logs/history/command_history.jsonl`) and resend last command
- Minimal desktop pet floating window with transparent topmost drag, tray show/hide, right-click pause/resume, click-to-open control center, remembered position, optional animation, and runtime status text expressions

**Planned**

- ChatGPT / Cursor drivers · LLM routing · read-aloud of Codex replies · installer packaging, etc.

## Developer docs

- Agent guide: [`AGENTS.md`](AGENTS.md) (English, for AI agents)
- Chinese notes: [`AGENTS_CN.md`](AGENTS_CN.md)
