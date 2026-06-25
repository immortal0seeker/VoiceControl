<div align="right">

[中文](README.md) | **[English](README_EN.md)**

</div>

# VoiceControl

A local voice desktop assistant for Windows 11 (MVP). Wake word → record → transcribe → send to Codex Desktop automatically.

```text
hey jarvis → beep → speak command → auto-stop on silence → Whisper STT → paste into Codex
```

## Requirements

- Windows 11
- Python 3.11+ (use the project `.venv` only — do not use global Python)
- Microphone
- NVIDIA GPU optional (Whisper defaults to `cuda`/`float16`; falls back to CPU automatically)
- [Codex Desktop](https://openai.com/codex) must be **running first** (may be minimized; the app focuses the window automatically)

## Installation

```powershell
cd <project-directory>
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\pip.exe install -e .
```

`pip install -e .` installs the `voicecontrol` package in editable mode so `python -m voicecontrol.*` works from any directory.

The first run downloads Whisper and openWakeWord models; an internet connection is required.

## Usage

### Settings UI

```powershell
.venv\Scripts\python.exe -m voicecontrol.ui.settings_app
```

The settings UI only reads and writes the root `config.json`. Restart the tray/listener process after saving changes.

### Daily use (tray daemon, recommended)

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app
```

A blue **V** icon appears in the system tray. Right-click menu: pause/resume listening, toggle launch-at-logon, quit.

Logs: `logs\voicecontrol.log`

### Foreground debug (console output)

```powershell
# Wake-word mode
.venv\Scripts\python.exe -m voicecontrol.main --wake

# Transcribe only; do not send to Codex
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
```

Say **"hey jarvis"** (English) → hear a beep → speak your command in Chinese → recording stops after ~3 s of silence.

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
```

## Configuration

All tunables live in [`src/voicecontrol/config/settings.py`](src/voicecontrol/config/settings.py). Common options:

| Parameter | Default | Description |
| --- | --- | --- |
| `WAKE_WORD_MODEL` | `hey_jarvis` | Wake-word model |
| `wake_word.model` | `hey_jarvis` | Select `hey_jarvis` or bundled custom `world_activate` in `config.json` / settings UI |
| `WAKE_THRESHOLD` | `0.5` | Wake sensitivity (lower = more sensitive) |
| `VAD_SILENCE_DURATION` | `3.0` | Trailing silence before stop (seconds) |
| `CODEX_WINDOW_TITLE` | `Codex` | Window title substring to match |
| `WHISPER_MODEL_SIZE` | `small` | Upgrade path: `medium` / `large-v3` |

## Project layout

```text
src/voicecontrol/
├── main.py           CLI entry (--once / --vad / --wake / --no-send)
├── tray_app.py       System-tray daemon
├── config/settings.py
├── audio/            Microphone & recording
├── stt/              faster-whisper
├── vad/              Silero VAD endpointing
├── wake_word/        openWakeWord
├── executor/         Codex window focus + paste
├── pipeline/         Orchestration
└── utils/            Beeps, launch-at-logon
```

## Feature status

**Shipped (MVP)**

- Microphone capture and faster-whisper transcription (Chinese / English)
- Hotkey trigger (F9 start/stop) and VAD auto-stop on silence
- Wake word “hey jarvis” plus system-tray background daemon
- Auto-focus Codex Desktop and paste commands

**Planned**

- Text-to-speech · ChatGPT / Cursor drivers · LLM routing, etc.

## Developer docs

- Agent guide: [`AGENTS.md`](AGENTS.md) (English, for AI agents)
- Chinese notes: [`AGENTS_CN.md`](AGENTS_CN.md)
