<div align="right">

**[中文](README.md)** | [English](README_EN.md)

</div>

# VoiceControl

Windows 11 本地语音桌面助手。说唤醒词 → 录音 → 转写 → 自动发送到 Codex Desktop。

```text
hey jarvis（或 world_activate）→ 蜂鸣 / TTS「我在」→ 说命令 → 静音自动停录 → Whisper 转写 → 粘贴到 Codex
```

## 环境要求

- Windows 11
- Python 3.11+（仅用项目 `.venv`，不要用全局 Python）
- 麦克风
- NVIDIA GPU 可选（Whisper 默认 `cuda`/`float16`，无 GPU 时自动降级 CPU）
- [Codex Desktop](https://openai.com/codex) 需**先启动**（可最小化；也可在 `config.json` 配置 `codex_launch_command` 自动启动）

## 安装

```powershell
cd <项目目录>
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\pip.exe install -e .
```

`pip install -e .` 会以可编辑模式安装 `voicecontrol` 包，之后可在任意目录使用 `python -m voicecontrol.*`。

首次运行会下载 Whisper 与 openWakeWord 模型，需联网。捆绑的自定义唤醒词 `world_activate.onnx` 已随包分发。

## 运行

### 设置页

```powershell
.venv\Scripts\python.exe -m voicecontrol.ui.settings_app
```

也可从托盘右键菜单 **「打开设置」** 或双击托盘图标启动（独立进程）。

设置页读写根目录 `config.json`，保存后**重启托盘/监听进程**生效。控制中心左侧导航包括 5 页：录音/状态控制、设置（含 TTS）、诊断、命令历史、日志查看。

### 日常使用（托盘后台，推荐）

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app
```

任务栏出现 **V** 图标（优先加载 `ui/assets/app_icon.png`）。右键菜单：

- 暂停 / 恢复监听
- 开始 / 停止录音（跳过唤醒词，直接录命令）
- 打开设置
- 开关开机自启
- 退出

双击托盘图标会打开设置/控制中心。托盘日志：`logs\tray\YYYYMMDD_voicecontrol.log`（按日一个文件）。

启用 TTS 时，流水线状态会播报短句（如「我在」「请说」「正在识别」「已发送」）。

### 桌面宠物状态窗

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.ui.desktop_pet_app
```

桌宠是最小透明置顶悬浮窗：可拖动，左键点击打开控制中心，右键可打开控制中心或退出。它每秒读取 `logs\runtime\runtime_status.json`，根据监听、录音、发送、出错等状态切换文字表情。

### 前台调试（有控制台输出）

`main.py` 现在定位为开发调试 CLI，日常使用优先启动托盘。

```powershell
# 唤醒词模式
.venv\Scripts\python.exe -m voicecontrol.main --wake

# 只转写，不发送到 Codex
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
```

说唤醒词（默认 **"hey jarvis"** 英文，或设置页选 **world_activate**）→ 听到蜂鸣 / TTS → 说中文命令 → 静音约 3 秒后自动结束；录音中可按 **F9** 提前停止。

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

# 查看自启状态与启动命令
.venv\Scripts\python.exe -m voicecontrol.utils.autostart
```

设置 UI 内也提供麦克风、VAD、唤醒词文件、TTS、Codex 发送测试与近期日志查看。

## 配置

用户配置在根目录 [`config.json`](config.json)，由 [`src/voicecontrol/config/manager.py`](src/voicecontrol/config/manager.py) 与代码默认值合并，运行时经 [`settings.py`](src/voicecontrol/config/settings.py) 导出。

常用项：

| 参数 / config.json 键 | 默认 | 说明 |
| --- | --- | --- |
| `wake_word.model` | `hey_jarvis` | 唤醒词；可选捆绑的 `world_activate` |
| `wake_word.threshold` | `0.5` | 唤醒灵敏度（越低越敏感） |
| `wake_word.cooldown` | `2.0` | 上一条命令结束后忽略重复唤醒的秒数 |
| `vad.silence_duration` | `3.0` | 说完后静音多久停止录音（秒） |
| `executor.codex_window_title` | `Codex` | 窗口标题匹配子串 |
| `executor.codex_launch_command` | `""` | 窗口缺失时执行的启动命令 |
| `stt.whisper_model_size` | `small` | 可升级 `medium` / `large-v3` |
| `tts.enabled` | `true` | Windows SAPI 状态短句播报 |
| `hotkeys.record_hotkey` | `f9` | 热键模式录音键；唤醒循环中也可手动停录 |

## 项目结构

```text
config.json
src/voicecontrol/
├── main.py           CLI 入口（--once / --vad / --wake / --no-send）
├── tray_app.py       系统托盘常驻
├── config/           settings.py, manager.py
├── audio/            麦克风、录音
├── stt/              faster-whisper
├── vad/              Silero VAD 端点检测
├── wake_word/        openWakeWord + models/world_activate.onnx
├── executor/         Codex 窗口聚焦 + 粘贴
├── pipeline/         流程编排、状态事件
├── control/          托盘文件命令（logs/runtime/control_command.json）
├── events/           状态 pub/sub + runtime 状态快照
├── history/          命令历史 JSONL
├── diagnostics/      自测工具
├── tts/              Windows SAPI 状态播报
├── ui/               PySide6 控制中心界面
│   ├── desktop_pet.py     桌宠悬浮窗
│   └── desktop_pet_app.py 桌宠启动入口
└── utils/            蜂鸣、开机自启、热键
logs/
├── tray/             按日托盘日志（YYYYMMDD_voicecontrol.log）
├── history/          command_history.jsonl
├── diagnostics/      diagnostics.jsonl
└── runtime/          runtime_status.json、control_command.json
```

## 功能状态

**已实现**

- 麦克风录音与 faster-whisper 语音转写（中/英）
- 热键触发（F9 开始/停止）与 VAD 静音自动停录
- 唤醒词（`hey_jarvis` / 捆绑 `world_activate`）+ 系统托盘后台常驻
- 托盘手动录音、暂停/恢复、开机自启、双击打开设置
- 自动聚焦 Codex Desktop 并粘贴命令；可选自动启动 Codex
- PySide6 控制中心（`config.json`）
- Windows SAPI 流水线状态 TTS（短句）
- runtime 状态快照（`logs/runtime/runtime_status.json`），录音页每秒刷新
- 命令历史（`logs/history/command_history.jsonl`）与重发上一条
- 桌宠最小悬浮窗：透明置顶、可拖动、点击打开控制中心、根据 runtime 状态切换文字表情

**计划中**

- ChatGPT / Cursor 驱动 · LLM 路由 · 朗读 Codex 回复全文 · 安装包等

## 开发文档

- Agent 指南：[`AGENTS.md`](AGENTS.md)（英文，供 AI Agent 使用）
- 中文说明：[`AGENTS_CN.md`](AGENTS_CN.md)
