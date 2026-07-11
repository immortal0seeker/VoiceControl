# AGENTS_CN.md - VoiceControl

> 本文件是 [`AGENTS.md`](AGENTS.md) 的中文说明版。Agent 工作时仍以英文版为准。

VoiceControl 是面向 Windows 11 的本地语音驱动桌面自动化助手。MVP 已交付，当前 post-MVP 工作重点是多目标执行器、设置 UI、TTS 状态提示、诊断、命令历史和桌宠体验。

端到端目标：

```text
说话 -> 唤醒词 -> 录音 -> 语音转文字 -> 路由命令
     -> 发送到 Codex / ChatGPT / Cursor / Trae -> 执行任务 -> 可选 TTS
```

这是一个由语音驱动的本地桌面自动化系统，不是通用聊天机器人。

---

## 1. 环境

```text
系统       Windows 11
Python     3.11+（只使用 .venv，不使用全局 Python）
GPU        推荐 NVIDIA CUDA；支持 CPU int8 兜底
Shell      PowerShell（链式命令用 ';'，不要用 '&&'）
```

在 `.venv` 内安装：

```powershell
pip install -r requirements.txt
pip install -e .
```

可编辑安装会注册 `voicecontrol` 包，之后可以在任意目录运行 `python -m voicecontrol.*`。

---

## 2. 项目决策

| 主题 | 决策 |
| --- | --- |
| STT 引擎 | 通过 `create_stt_engine()` provider factory 选择；默认 `faster_whisper`，可选 `funasr_sensevoice` |
| 语言 | 中文为主 + 英文，使用多语言模型 |
| 默认 STT 模型 | Whisper `small`；可选 Whisper `medium`、SenseVoice-Small |
| 计算 | GPU 优先：`cuda` / `float16`；CPU 兜底：`int8` |
| 用户配置 | 根目录 `config.json` 覆盖代码默认值；`config/manager.py` 合并；`settings.py` 导出 |
| Executor 目标 | ChatGPT（兼容键 `codex`）、ChatGPT Classic（兼容键 `chatgpt`）、Cursor、Trae |
| Executor 设计 | 可插拔 `AppDriver`；复用 `LaunchableAppDriver`；由 `executor/router.py` 选择目标 |
| VAD | faster-whisper 附带的 Silero VAD ONNX，通过 onnxruntime 使用 |
| 唤醒词 | openWakeWord ONNX；内置 `hey_jarvis` 或自定义 `world_activate.onnx` |
| TTS | Windows SAPI via `pywin32`；只播报短状态提示，不朗读完整回复 |
| 后台模式 | `pythonw` 托盘程序；HKCU Run 开机自启；不是 Windows Service |
| 进程间控制 | `logs/runtime/control_command.json` 文件命令，`logs/runtime/control_response.json` 写回确认 |

---

## 3. 已交付功能

```text
调试 CLI 单次录音       python -m voicecontrol.main --once
调试 CLI 热键触发       F9 开始/停止，Esc 退出
VAD 自动停录            热键循环加 --vad
唤醒词 + 托盘           --wake 或 pythonw -m voicecontrol.tray_app
目标应用路由            executor.default_target = codex / chatgpt / cursor / trae
Codex driver            聚焦 -> 点击输入框 -> 粘贴 -> Enter；支持自动启动
ChatGPT driver          聚焦 -> Ctrl+Shift+L -> 粘贴 -> Enter；支持自动启动
Cursor driver           聚焦 -> Ctrl+Shift+L -> 粘贴 -> Enter；支持自动启动
Trae driver             聚焦 -> 底部中性区域点击 -> Ctrl+U -> 粘贴 -> Enter；支持自动启动
控制中心                python -m voicecontrol.ui.settings_app
桌宠                    pythonw -m voicecontrol.ui.desktop_pet_app
开机自启                托盘菜单切换
TTS 状态提示            按流水线事件播报短句
Runtime 状态            logs/runtime/runtime_status.json
命令历史                logs/history/command_history.jsonl
诊断                    麦克风 / VAD / 唤醒词 / STT 模型对比 / SenseVoice 资源 / TTS / 默认目标发送测试
手动录音                托盘或设置页写入控制命令，跳过唤醒词
自定义唤醒词            bundled world_activate.onnx
```

典型生产流程：

```text
托盘守护 -> 听到唤醒词 -> 蜂鸣/TTS 提示 -> 录音 -> 转写
-> 路由到配置的 AppDriver -> 粘贴发送 -> 写历史 + 完成提示
```

运行命令：

```powershell
.venv\Scripts\python.exe -m voicecontrol.main --wake
.venv\Scripts\python.exe -m voicecontrol.main --wake --no-send
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app
.venv\Scripts\python.exe -m voicecontrol.ui.settings_app
.venv\Scripts\pythonw.exe -m voicecontrol.ui.desktop_pet_app
```

托盘日志：`logs/tray/YYYYMMDD_voicecontrol.log`。

---

## 4. 仓库结构

按需创建文件，不提前搭空模块。始终使用 `voicecontrol.*` 绝对导入，不使用 `src.*`。

```text
VoiceControl/
├── config.json
├── audio_files/                 recordings/, temp/, samples/（git 忽略）
├── logs/                        tray/, history/, diagnostics/, runtime/（git 忽略）
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
    ├── stt/                 STTEngine 协议、WhisperEngine、SenseVoiceEngine、provider factory
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

模块边界：

- `audio/`：设备列表、录音、保存/播放 WAV、音频校验；不放 STT/VAD/唤醒词逻辑。
- `stt/`：加载 Whisper、转写文件、规范化结果；不放麦克风逻辑。
- `executor/`：聚焦目标窗口、发送文本、模拟输入；不放录音/STT 逻辑。
- `pipeline/`：编排下层模块；依赖 `AppDriver`，不依赖具体 driver。
- `config/`：默认值和用户配置合并。
- `control/`：文件式托盘 IPC 命令。
- `events/`：状态 pub/sub 和 runtime 状态快照。
- `history/`：追加式命令历史和重发；读取时跳过并记录损坏的 JSONL 行，不能让单行损坏遮蔽后续有效历史。
- `diagnostics/`：设置 UI 或 CLI 中的自测工具，包括 SenseVoice 资源基准；`nvidia-smi` 等可选工具缺失时应报告不可用，而不是让诊断失败；UI 发起的诊断必须离开 Qt GUI 线程运行。
- `tts/`：Windows SAPI 状态短句。
- `ui/`：PySide6 控制中心和桌宠；不放 pipeline 逻辑。
- `utils/`：仅放无处归属的通用辅助。

---

## 5. 关键配置

运行值来自合并后的 `config.json`。修改后需要重启托盘/监听进程。

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

`config.json` 当前包含 ChatGPT（原 Codex 包）、ChatGPT Classic、Cursor、Trae 的 AppsFolder 启动命令，四者均已实测完成打开、聚焦/注入文本和发送闭环。内部 `codex` / `chatgpt` 目标键为兼容已有配置而保留。

STT 默认仍保持 `faster_whisper` + Whisper `small`。SenseVoice-Small 已通过 `stt.provider = "funasr_sensevoice"` 和设置 UI 接入，但 FunASR 运行时暂未加入默认安装依赖；缺少 SenseVoice 依赖时，诊断应给出清晰的单模型错误，同时保留 Whisper 对比结果。根目录 `config.json` 可作为本机用户配置启用 SenseVoice-Small + `cuda`；不要把 `DEFAULT_CONFIG` 从 `faster_whisper` + Whisper `small` 改掉。

---

## 6. Executor 设计

不要在 pipeline/history/diagnostics 中硬编码目标应用，统一走 driver 抽象和 router。

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

规则：

- 默认目标通过 `voicecontrol.executor.router.get_default_driver()` 获取。
- 显式目标通过 `create_driver("codex" | "chatgpt" | "cursor" | "trae")` 创建。
- 优先用剪贴板粘贴，而不是逐字输入。
- ChatGPT Classic 和 Cursor 使用 `Ctrl+Shift+L` 聚焦输入区。
- Trae 先点击底部中性区域让 AI 侧栏失焦，再用 `Ctrl+U` 聚焦 AI 输入框；`Ctrl+U` 后不要再点击输入框。
- ChatGPT（原 Codex）仍使用相对输入框点击坐标；窗口查找必须先做不区分大小写的精确匹配，再做子串兜底。
- 桌面操作前后保留短延迟和清晰日志。
- 注意焦点丢失、输入法、管理员权限边界、编辑器热键截获。

---

## 7. 编码规则

- 简单、可读、小函数，显式优先。
- 公共函数/方法尽量加类型提示。
- 路径用 `pathlib.Path`。
- 可复用模块用 `logging`；`print` 只用于 CLI/debug 入口。
- 命名：文件/函数/变量/模块用 `snake_case`，类用 `PascalCase`，常量用 `UPPER_CASE`。
- 避免不必要的全局可变状态。
- 工作区可能有用户改动；不要回滚无关修改。

---

## 8. 错误处理

显式处理 Windows 失败场景，不要静默吞掉：

```text
麦克风不可用、设备索引无效、音频文件缺失、
模型加载失败、转写为空、窗口未找到、
启动失败、权限拒绝、热键冲突、TTS/SAPI 不可用
```

可复用模块应抛出清晰异常或记录日志。CLI 入口可以打印用户可读错误。

---

## 9. 依赖

运行依赖在 `requirements.txt`，并与 `pyproject.toml` 同步。新增依赖要有明确理由，优先稳定常用包，避免重复。

SenseVoice-Small 运行时是可选依赖，必须保持在默认依赖之外：

```powershell
.venv\Scripts\pip.exe install -e ".[sensevoice]"
```

Windows NVIDIA GPU 实测路径需要把通用 CPU wheel 替换为匹配的 CUDA 12.8 wheel：

```powershell
.venv\Scripts\pip.exe install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
.venv\Scripts\pip.exe install --force-reinstall --no-deps torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu128
```

`sensevoice` extra 包含 FunASR/ModelScope/Torch/Torchaudio。`DEFAULT_CONFIG` 默认保持 `stt.sensevoice_device = "cpu"`，避免长期托盘/监听默认占用 GPU 显存；用户根目录 `config.json` 可在安装 extra 和 CUDA 版 PyTorch 后改为 `stt.sensevoice_device = "cuda"`。SenseVoice engine 必须保持懒加载；仅安装 extra 或启动托盘不应导入 Torch，只有选择 SenseVoice 并实际请求转写时才加载。配置为 CUDA 但 `torch.cuda.is_available()` 为 false 时必须清晰报错并停止本次转写，禁止静默退回 CPU。

打包资源：

```text
ui/assets/*
wake_word/models/*
```

---

## 10. 暂不在范围内

```text
完整对话式 TTS
LLM 意图路由
CLI agent driver
打包安装器
首次运行自动发现应用
真正 Windows Service
transcribe_array
默认安装中捆绑 FunASR/SenseVoice 运行时
```

---

## 11. Agent 行为准则

1. 先读 `README.md` 和本文件；创建文件前先看目录结构。
2. 做最小有用改动，并保持项目可运行。
3. 一个能工作的垂直切片胜过多个半成品模块。
4. 保持命名约定，不重写无关文件。
5. 给出用户应运行的准确 PowerShell 命令。
6. 对不确定的 Windows 音频行为，先写诊断脚本。

开发哲学：先跑起来 -> 可观察 -> 稳定 -> 快 -> 智能。
