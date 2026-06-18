<div align="right">

**[中文](README.md)** | [English](README_EN.md)

</div>

# VoiceControl

Windows 11 本地语音桌面助手（MVP）。说唤醒词 → 录音 → 转写 → 自动发送到 Codex Desktop。

```text
hey jarvis → 蜂鸣 → 说命令 → 静音自动停录 → Whisper 转写 → 粘贴到 Codex
```

## 环境要求

- Windows 11
- Python 3.11+（仅用项目 `.venv`，不要用全局 Python）
- 麦克风
- NVIDIA GPU 可选（Whisper 默认 `cuda`/`float16`，无 GPU 时自动降级 CPU）
- [Codex Desktop](https://openai.com/codex) 需**先启动**（可最小化；程序会自动聚焦窗口）

## 安装

```powershell
cd <项目目录>
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\pip.exe install -e .
```

`pip install -e .` 会以可编辑模式安装 `voicecontrol` 包，之后可在任意目录使用 `python -m voicecontrol.*`。

首次运行会下载 Whisper 与 openWakeWord 模型，需联网。

## 运行

### 日常使用（托盘后台，推荐）

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app
```

任务栏出现蓝色 **V** 图标。右键菜单：暂停/恢复监听、开关开机自启、退出。

日志：`logs\voicecontrol.log`

### 前台调试（有控制台输出）

```powershell
# 唤醒词模式
.venv\Scripts\python.exe -m voicecontrol.main --wake

# 只转写，不发送到 Codex
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
```

说 **"hey jarvis"**（英文）→ 听到蜂鸣 → 说中文命令 → 静音约 3 秒后自动结束。

### 热键模式（无唤醒词）

```powershell
# 单次固定时长录音（默认 5 秒）
.venv\Scripts\python.exe -m voicecontrol.main --once

# F9 开始/停止，Esc 退出
.venv\Scripts\python.exe -m voicecontrol.main

# F9 开始，说完自动停止
.venv\Scripts\python.exe -m voicecontrol.main --vad
```

### 诊断

```powershell
# 列出麦克风设备
.venv\Scripts\python.exe -m voicecontrol.audio.device_manager

# 列出可见窗口（查 Codex 标题）
.venv\Scripts\python.exe -m voicecontrol.executor.window_utils
```

## 配置

所有可调参数在 [`src/voicecontrol/config/settings.py`](src/voicecontrol/config/settings.py)，常用项：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `WAKE_WORD_MODEL` | `hey_jarvis` | 唤醒词模型 |
| `WAKE_THRESHOLD` | `0.5` | 唤醒灵敏度（越低越敏感） |
| `VAD_SILENCE_DURATION` | `3.0` | 说完后静音多久停止录音（秒） |
| `CODEX_WINDOW_TITLE` | `Codex` | 窗口标题匹配子串 |
| `WHISPER_MODEL_SIZE` | `small` | 可升级 `medium` / `large-v3` |

## 项目结构

```text
src/voicecontrol/
├── main.py           CLI 入口（--once / --vad / --wake / --no-send）
├── tray_app.py       系统托盘常驻
├── config/settings.py
├── audio/            麦克风、录音
├── stt/              faster-whisper
├── vad/              Silero VAD 端点检测
├── wake_word/        openWakeWord
├── executor/         Codex 窗口聚焦 + 粘贴
├── pipeline/         流程编排
└── utils/            蜂鸣反馈、开机自启
```

## 功能状态

**已实现（MVP）**

- 麦克风录音与 faster-whisper 语音转写（中/英）
- 热键触发（F9 开始/停止）与 VAD 静音自动停录
- 唤醒词「hey jarvis」+ 系统托盘后台常驻
- 自动聚焦 Codex Desktop 并粘贴命令

**计划中**

- 语音播报（TTS）· ChatGPT / Cursor 驱动 · LLM 路由等

## 开发文档

- Agent 指南：[`AGENTS.md`](AGENTS.md)（英文，供 AI Agent 使用）
- 中文说明：[`AGENTS_CN.md`](AGENTS_CN.md)
