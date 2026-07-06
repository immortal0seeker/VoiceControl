<div align="right">

[中文](README.md) | **English**

</div>

# VoiceControl

VoiceControl is a local voice-driven desktop assistant for Windows 11. After a wake word, it records your command, transcribes it with local STT, and sends it to the configured target app.

```text
hey jarvis / world_activate -> beep or TTS "I'm here"
-> speak command -> VAD auto-stop -> STT transcription
-> send to Codex / ChatGPT / Cursor / Trae
```

It is a local desktop automation system, not a general chatbot.

## Requirements

- Windows 11
- Python 3.11+, using only the project `.venv`
- Microphone
- NVIDIA GPU optional; CPU fallback is supported
- At least one target desktop app installed as needed: Codex Desktop, ChatGPT Desktop, Cursor, or Trae

## Installation

```powershell
cd <project-directory>
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\pip.exe install -e .
```

`pip install -e .` registers the `voicecontrol` package so `python -m voicecontrol.*` works from any directory.

The first Whisper / openWakeWord run may need to download models. The custom wake word model `world_activate.onnx` is bundled.

STT defaults to `faster_whisper` + Whisper `small`. The settings UI also offers Whisper `medium` and SenseVoice-Small; SenseVoice-Small requires the FunASR runtime, which is not bundled in the default install yet.

## Usage

### Control Center

```powershell
.venv\Scripts\python.exe -m voicecontrol.ui.settings_app
```

The control center edits `config.json`. Restart the tray/listener process after saving.

The Executor card can choose the default target app:

```text
codex | chatgpt | cursor | trae
```

### Daily Use: Tray Daemon

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app
```

The tray menu supports:

- Pause / resume listening
- Start / stop recording
- Open settings
- Show / hide desktop pet
- Launch at logon
- Quit

Tray logs:

```text
logs\tray\YYYYMMDD_voicecontrol.log
```

### Desktop Pet

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.ui.desktop_pet_app
```

The desktop pet reads `logs\runtime\runtime_status.json` and changes its display for listening, recording, sending, and error states.

### Foreground Debug

```powershell
.venv\Scripts\python.exe -m voicecontrol.main --wake
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
```

### Hotkey Mode

```powershell
.venv\Scripts\python.exe -m voicecontrol.main --once
.venv\Scripts\python.exe -m voicecontrol.main
.venv\Scripts\python.exe -m voicecontrol.main --vad
```

Default hotkeys: `F9` starts/stops recording, `Esc` quits.

## Target Apps And Launch Commands

`executor.default_target` in `config.json` controls where voice commands are sent by default:

```json
"default_target": "cursor"
```

Supported values:

```text
codex
chatgpt
cursor
trae
```

The current config includes AppsFolder launch commands:

```json
"codex_launch_command": "explorer.exe shell:AppsFolder\\OpenAI.Codex_2p2nqsd0c76g0!App",
"chatgpt_launch_command": "explorer.exe shell:AppsFolder\\OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0!ChatGPT",
"cursor_launch_command": "explorer.exe shell:AppsFolder\\Anysphere.Cursor",
"trae_launch_command": "explorer.exe shell:AppsFolder\\ByteDance.TraeCN"
```

Notes:

- Codex Desktop, ChatGPT Desktop, Cursor, and Trae have been live-tested for opening, focusing/injecting text, and sending prompts.
- ChatGPT Desktop and Cursor use `Ctrl+Shift+L` to focus the composer.
- Trae uses a bottom neutral click to clear stale AI-sidebar focus, then `Ctrl+U` to focus the AI input, then paste/Enter. It does not click again after `Ctrl+U`.
- Codex still uses relative composer click coordinates.
- If a target window is missing and its launch command is configured, the driver tries to start the app and waits for a matching window.

## Diagnostics

```powershell
.venv\Scripts\python.exe -m voicecontrol.audio.device_manager
.venv\Scripts\python.exe -m voicecontrol.executor.window_utils
.venv\Scripts\python.exe -m voicecontrol.utils.autostart
```

The control center also provides microphone, VAD, wake-word, STT model comparison, TTS, default-target send tests, and log viewing. STT comparison runs Whisper `small`, Whisper `medium`, and SenseVoice-Small; if the SenseVoice runtime is missing, it shows a per-model error while preserving Whisper results.

## Common Configuration

| Config key | Default/example | Description |
| --- | --- | --- |
| `wake_word.model` | `hey_jarvis` | Wake word model; `world_activate` is bundled |
| `wake_word.threshold` | `0.5` | Wake sensitivity |
| `vad.silence_duration` | `3.0` | Trailing silence before recording stops |
| `executor.default_target` | `cursor` | Default send target |
| `executor.codex_window_title` | `Codex` | Codex window-title match |
| `executor.chatgpt_window_title` | `ChatGPT` | ChatGPT window-title match |
| `executor.cursor_window_title` | `Cursor` | Cursor window-title match |
| `executor.trae_window_title` | `Trae` | Trae window-title match |
| `stt.provider` | `faster_whisper` | STT provider: `faster_whisper` / `funasr_sensevoice` |
| `stt.whisper_model_size` | `small` | Whisper model tier: `small` / `medium` |
| `stt.sensevoice_model` | `SenseVoiceSmall` | SenseVoice-Small config; requires extra FunASR runtime |
| `tts.enabled` | `true` | Windows SAPI short status phrases |
| `hotkeys.record_hotkey` | `f9` | Recording hotkey |

## Project Layout

```text
config.json
src/voicecontrol/
├── main.py
├── tray_app.py
├── config/
├── audio/
├── stt/
├── vad/
├── wake_word/
├── executor/
│   ├── app_driver.py
│   ├── router.py
│   ├── codex_driver.py
│   ├── chatgpt_driver.py
│   ├── cursor_driver.py
│   ├── trae_driver.py
│   └── window_utils.py
├── pipeline/
├── control/
├── events/
├── history/
├── diagnostics/
├── tts/
├── ui/
└── utils/
logs/
├── tray/
├── history/
├── diagnostics/
└── runtime/
```

## Feature Status

Shipped:

- Microphone capture and STT transcription, defaulting to faster-whisper
- STT provider factory, Whisper small/medium, SenseVoice-Small engine, and model comparison diagnostics
- F9 hotkey recording and VAD auto-stop
- openWakeWord wake-word loop and tray daemon
- Codex / ChatGPT / Cursor / Trae desktop drivers, with all four live send loops verified
- Default target-app routing
- AppsFolder launch-command config
- PySide6 control center
- Windows SAPI status TTS
- Runtime status snapshot
- Command history and resend
- Desktop pet status window
- Diagnostics and logs pages

Planned:

- Small desktop task abilities
- Custom desktop-pet avatars
- Packaging and startup experience
- Formal SenseVoice/FunASR dependency installation and release path
- Stability and diagnostics improvements
- Smarter voice routing
- CLI agent driver

## Developer Docs

- Agent guide: [AGENTS.md](AGENTS.md)
- Agent Chinese notes: [AGENTS_CN.md](AGENTS_CN.md)
- Chinese README: [README.md](README.md)
