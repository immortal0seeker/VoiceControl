<div align="right">

**中文** | [English](README_EN.md)

</div>

# VoiceControl

VoiceControl 是 Windows 11 本地语音桌面助手：说出唤醒词后录音，使用 Whisper 转写，再把命令发送到配置的目标应用。

```text
hey jarvis / world_activate -> 蜂鸣或 TTS「我在」
-> 说命令 -> VAD 自动停录 -> Whisper 转写
-> 发送到 Codex / ChatGPT / Cursor / Trae
```

它是本地桌面自动化系统，不是通用聊天机器人。

## 环境要求

- Windows 11
- Python 3.11+，只使用项目 `.venv`
- 麦克风
- NVIDIA GPU 可选；无 GPU 时使用 CPU fallback
- 目标桌面应用：Codex Desktop、ChatGPT Desktop、Cursor、Trae 至少按需安装其一

## 安装

```powershell
cd <项目目录>
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\pip.exe install -e .
```

`pip install -e .` 会注册 `voicecontrol` 包，之后可以使用 `python -m voicecontrol.*`。

首次使用 Whisper / openWakeWord 时可能需要下载模型。项目已内置自定义唤醒词模型 `world_activate.onnx`。

## 运行

### 控制中心

```powershell
.venv\Scripts\python.exe -m voicecontrol.ui.settings_app
```

控制中心可修改 `config.json`。保存后需要重启托盘/监听进程才生效。

设置页的 Executor 卡片可以选择默认目标应用：

```text
codex | chatgpt | cursor | trae
```

### 日常托盘后台

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app
```

托盘菜单支持：

- 暂停 / 恢复监听
- 开始 / 停止录音
- 打开设置
- 显示 / 隐藏桌宠
- 开机自启
- 退出

托盘日志位于：

```text
logs\tray\YYYYMMDD_voicecontrol.log
```

### 桌宠

```powershell
.venv\Scripts\pythonw.exe -m voicecontrol.ui.desktop_pet_app
```

桌宠会读取 `logs\runtime\runtime_status.json`，按监听、录音、发送、错误等状态切换显示。

### 前台调试

```powershell
.venv\Scripts\python.exe -m voicecontrol.main --wake
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
```

### 热键模式

```powershell
.venv\Scripts\python.exe -m voicecontrol.main --once
.venv\Scripts\python.exe -m voicecontrol.main
.venv\Scripts\python.exe -m voicecontrol.main --vad
```

默认热键：`F9` 开始/停止录音，`Esc` 退出。

## 目标应用与启动命令

`config.json` 的 `executor.default_target` 决定语音命令默认发送到哪个应用：

```json
"default_target": "cursor"
```

可选值：

```text
codex
chatgpt
cursor
trae
```

当前配置已写入 AppsFolder 启动命令：

```json
"codex_launch_command": "explorer.exe shell:AppsFolder\\OpenAI.Codex_2p2nqsd0c76g0!App",
"chatgpt_launch_command": "explorer.exe shell:AppsFolder\\OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0!ChatGPT",
"cursor_launch_command": "explorer.exe shell:AppsFolder\\Anysphere.Cursor",
"trae_launch_command": "explorer.exe shell:AppsFolder\\ByteDance.TraeCN"
```

说明：

- Codex Desktop、ChatGPT Desktop、Cursor 已经实测可以成功发送消息。
- Trae 已有初版 driver 和路由支持，并使用独立的输入框点击坐标，但真实发送闭环尚待验证。
- ChatGPT Desktop 和 Cursor 使用 `Ctrl+Shift+L` 聚焦输入区；Codex 和 Trae 暂时使用相对位置点击输入框。
- 如果窗口不存在且启动命令不为空，driver 会尝试启动应用并等待窗口出现。

## 诊断

```powershell
.venv\Scripts\python.exe -m voicecontrol.audio.device_manager
.venv\Scripts\python.exe -m voicecontrol.executor.window_utils
.venv\Scripts\python.exe -m voicecontrol.utils.autostart
```

控制中心也提供麦克风、VAD、唤醒词、TTS、默认目标发送测试和日志查看。

## 常用配置

| 配置键 | 默认/示例 | 说明 |
| --- | --- | --- |
| `wake_word.model` | `hey_jarvis` | 唤醒词模型，可选 `world_activate` |
| `wake_word.threshold` | `0.5` | 唤醒灵敏度 |
| `vad.silence_duration` | `3.0` | 说完后静音多久自动停录 |
| `executor.default_target` | `cursor` | 默认发送目标 |
| `executor.codex_window_title` | `Codex` | Codex 窗口标题匹配 |
| `executor.chatgpt_window_title` | `ChatGPT` | ChatGPT 窗口标题匹配 |
| `executor.cursor_window_title` | `Cursor` | Cursor 窗口标题匹配 |
| `stt.whisper_model_size` | `small` | 可升级为 `medium` / `large-v3` |
| `tts.enabled` | `true` | Windows SAPI 状态短句播报 |
| `hotkeys.record_hotkey` | `f9` | 录音热键 |

## 项目结构

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

## 功能状态

已实现：

- 麦克风录音与 faster-whisper 转写
- F9 热键录音与 VAD 自动停录
- openWakeWord 唤醒词和托盘后台
- Codex / ChatGPT / Cursor / Trae 桌面 driver（Trae 待实测发送闭环）
- 默认目标应用路由
- AppsFolder 启动命令配置
- PySide6 控制中心
- Windows SAPI 状态 TTS
- runtime 状态快照
- 命令历史与重发
- 桌宠状态窗口
- 诊断页和日志页

计划中：

- 桌面小任务能力
- 桌宠自定义形象
- 打包启动体验
- 稳定性/诊断增强
- 更智能的语音路由
- CLI agent driver

## 开发文档

- Agent 指南：[AGENTS.md](AGENTS.md)
- Agent 中文说明：[AGENTS_CN.md](AGENTS_CN.md)
- English README：[README_EN.md](README_EN.md)
