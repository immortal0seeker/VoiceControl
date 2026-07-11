<div align="right">

**中文** | [English](README_EN.md)

</div>

# VoiceControl

VoiceControl 是 Windows 11 本地语音桌面助手：说出唤醒词后录音，使用本地 STT 转写，再把命令发送到配置的目标应用。

```text
hey jarvis / world_activate -> 蜂鸣或 TTS「我在」
-> 说命令 -> VAD 自动停录 -> STT 转写
-> 发送到 Codex / ChatGPT / Cursor / Trae
```

它是本地桌面自动化系统，不是通用聊天机器人。

## 环境要求

- Windows 11
- Python 3.11+，只使用项目 `.venv`
- 麦克风
- NVIDIA GPU 可选；无 GPU 时使用 CPU fallback
- 目标桌面应用：ChatGPT（原 Codex）、ChatGPT Classic、Cursor、Trae 至少按需安装其一

## 安装

```powershell
cd <项目目录>
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\pip.exe install -e .
```

`pip install -e .` 会注册 `voicecontrol` 包，之后可以使用 `python -m voicecontrol.*`。

首次使用 Whisper / openWakeWord 时可能需要下载模型。项目已内置自定义唤醒词模型 `world_activate.onnx`。

STT 默认使用 `faster_whisper` + Whisper `small`。设置页也提供 Whisper `medium` 和 SenseVoice-Small 选项；SenseVoice-Small 需要额外安装 FunASR 运行时，默认安装暂不捆绑。

如需启用 SenseVoice-Small：

```powershell
.venv\Scripts\pip.exe install -e ".[sensevoice]"
```

如需在 Windows + NVIDIA GPU 上运行 SenseVoice，再安装项目已验证的 CUDA 12.8 wheel：

```powershell
.venv\Scripts\pip.exe install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
.venv\Scripts\pip.exe install --force-reinstall --no-deps torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu128
```

安装后用 `.venv\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"` 验证，最后一行必须是 `True`。如果配置为 `stt.sensevoice_device = "cuda"` 但 PyTorch 不支持 CUDA，VoiceControl 会明确报错并停止本次转写，不会静默退回 CPU。

资源边界：

- 未安装或未选择 SenseVoice-Small 时，不会导入 FunASR/Torch/Torchaudio，也不会占用额外 CPU、内存或显存。
- 默认 SenseVoice 配置是 CPU 模式：`stt.sensevoice_device = "cpu"`，不会占用 GPU 显存。
- 对已安装 `.[sensevoice]` 且显存充足的个人机器，可以在根目录 `config.json` 中设置 `stt.provider = "funasr_sensevoice"` 和 `stt.sensevoice_device = "cuda"`；这只影响本机用户配置，不改变仓库通用默认。
- 本地 spike 中 SenseVoice-Small 模型缓存约 896.5 MiB，VAD 模型约 3.8 MiB；Torch/FunASR 依赖本身体积也较大，适合作为可选安装。
- 选择 SenseVoice-Small 后，模型会在首次转写时懒加载；空闲监听阶段不做推理，CPU 主要在转写瞬间短时占用。
- 当前实现会复用已加载模型以降低后续延迟，因此会保留一部分内存占用。若长期后台内存压力明显，下一步应增加“空闲释放模型”或“按次加载”开关。
- RTX 4070 Laptop GPU 实测：CUDA 12.8 首次加载+转写约 27.55 秒，warm 转写约 0.095 秒，Python 进程 RSS 增加约 1.62 GiB，GPU 显存增加约 1140 MiB。

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

- ChatGPT（内部兼容键 `codex`）、ChatGPT Classic（内部兼容键 `chatgpt`）、Cursor、Trae 已经实测可以成功打开、聚焦/注入文本并发送消息。
- ChatGPT Classic 和 Cursor 使用 `Ctrl+Shift+L` 聚焦输入区。
- Trae 使用“底部中性区域点击失焦 -> `Ctrl+U` 聚焦 AI 输入框 -> 粘贴/回车”的策略；`Ctrl+U` 后不会再点击输入框。
- ChatGPT（原 Codex）当前仍使用相对位置点击输入框；窗口查找优先精确匹配，避免误选 ChatGPT Classic。
- 如果窗口不存在且启动命令不为空，driver 会尝试启动应用并等待窗口出现。

## 诊断

```powershell
.venv\Scripts\python.exe -m voicecontrol.audio.device_manager
.venv\Scripts\python.exe -m voicecontrol.executor.window_utils
.venv\Scripts\python.exe -m voicecontrol.utils.autostart
.venv\Scripts\python.exe -m voicecontrol.diagnostics.sensevoice_resource --audio audio_files\recordings\<sample>.wav --device cuda
```

控制中心也提供麦克风、VAD、唤醒词、STT 模型对比、TTS、默认目标发送测试和日志查看。耗时诊断在后台线程运行，不阻塞设置窗口。STT 对比会比较 Whisper `small`、Whisper `medium` 和 SenseVoice-Small；如果 SenseVoice 运行时未安装，会显示单模型错误并保留 Whisper 结果。

SenseVoice 资源诊断会用同一段 WAV 连续转写两次，记录 provider/model/device、音频路径、首次懒加载+转写耗时、warm 转写耗时、Python 进程 RSS 内存前后。如果系统有 `nvidia-smi`，还会记录 GPU 显存前后；没有 `nvidia-smi` 时该字段为 `null`，诊断不会因此失败。缺少 FunASR/SenseVoice 运行时时会写入清晰错误，并提示安装 optional extra。

## 常用配置

| 配置键 | 默认/示例 | 说明 |
| --- | --- | --- |
| `wake_word.model` | `hey_jarvis` | 唤醒词模型，可选 `world_activate` |
| `wake_word.threshold` | `0.5` | 唤醒灵敏度 |
| `vad.silence_duration` | `3.0` | 说完后静音多久自动停录 |
| `executor.default_target` | `cursor` | 默认发送目标 |
| `executor.codex_window_title` | `ChatGPT` | ChatGPT（原 Codex）窗口标题匹配 |
| `executor.chatgpt_window_title` | `ChatGPT Classic` | ChatGPT Classic 窗口标题匹配 |
| `executor.cursor_window_title` | `Cursor` | Cursor 窗口标题匹配 |
| `stt.provider` | `faster_whisper` | STT provider，可选 `faster_whisper` / `funasr_sensevoice` |
| `stt.whisper_model_size` | `small` | Whisper 档位，可选 `small` / `medium` |
| `stt.sensevoice_model` | `SenseVoiceSmall` | SenseVoice-Small 配置；需要额外 FunASR 运行时 |
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

- 麦克风录音与 STT 转写，默认 faster-whisper
- STT provider factory、Whisper small/medium、SenseVoice-Small engine 与诊断对比
- SenseVoice 资源占用诊断：cold/warm 耗时、RSS、可选 `nvidia-smi` 显存
- F9 热键录音与 VAD 自动停录
- openWakeWord 唤醒词和托盘后台
- ChatGPT / ChatGPT Classic / Cursor / Trae 桌面 driver，四目标发送闭环已实测（内部目标键保持兼容）
- 默认目标应用路由
- AppsFolder 启动命令配置
- PySide6 控制中心
- Windows SAPI 状态 TTS
- runtime 状态快照
- 命令历史与重发；损坏的 JSONL 行会记录警告并跳过，不影响后续有效记录
- 桌宠状态窗口
- 诊断页和日志页

计划中：

- 桌面小任务能力
- 桌宠自定义形象
- 打包启动体验
- SenseVoice/FunASR 正式依赖安装与发布路径
- SenseVoice 空闲释放模型 / 按次加载开关
- 稳定性/诊断增强
- 更智能的语音路由
- CLI agent driver

## 开发文档

- Agent 指南：[AGENTS.md](AGENTS.md)
- Agent 中文说明：[AGENTS_CN.md](AGENTS_CN.md)
- English README：[README_EN.md](README_EN.md)
