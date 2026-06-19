# AGENTS_CN.md — VoiceControl

> 本文档为 [`AGENTS.md`](AGENTS.md) 的中文版，供人类阅读；Agent 仍以英文版为准。

面向 Windows 11 的语音驱动 AI 桌面助手。本地 Python 项目；**MVP 已交付**。

端到端目标：

```text
说话 → 唤醒词 → 录音 → 语音转文字 → 路由命令
     → 发送到 Codex / ChatGPT / Cursor → 执行任务 → 可选 TTS
```

这是一个**由语音驱动的本地桌面自动化系统**，不是通用聊天机器人。

---

## 1. 环境

```text
操作系统   Windows 11
Python     3.11+  （仅使用 .venv — 切勿使用全局 Python）
GPU        推荐 NVIDIA CUDA（8 GB+ 显存可跑 Whisper small/medium）
           支持 CPU 兜底（int8）
Shell      PowerShell  （链式命令用 ';'，不要用 '&&'）
```

在 `.venv` 内安装：

```powershell
pip install -r requirements.txt
pip install -e .
```

可编辑安装会把项目注册为 `voicecontrol` 包，之后可在任意目录用
`python -m voicecontrol.*` 运行。

---

## 2. 项目决策（勿重复询问）

| 主题 | 决策 |
|------|------|
| STT 引擎 | `faster-whisper` |
| 语言 | 中文为主 + 英文（多语言模型） |
| 默认模型 | `small`（升级路径：`medium` → `large-v3`） |
| 计算设备 | GPU 优先：`device="cuda"`，`compute_type="float16"`；CPU 兜底（`int8`） |
| Executor 目标（按顺序） | Codex Desktop → ChatGPT Desktop → Cursor → 其它 |
| Executor 设计 | 可插拔 `AppDriver` 接口，每个目标应用一个驱动 |
| VAD 引擎 | 复用 faster-whisper 内置 Silero VAD ONNX（onnxruntime，无 torch） |
| 唤醒词引擎 | openWakeWord（ONNX/onnxruntime，无 torch/账号）；唤醒词 `hey_jarvis` 仅做激活，命令仍可中文 |
| 后台模式 | 系统托盘 `pythonw` + HKCU Run 开机自启。**不是** Windows Service（Session 0 无法操作桌面） |

---

## 3. 已交付功能（MVP）

```text
单次录音          python -m voicecontrol.main --once
热键触发          F9 开始/停止（默认循环）
VAD 自动停录      热键循环加 --vad
Codex 发送        聚焦 → 点输入框 → 粘贴 → Enter
唤醒词 + 托盘     --wake（前台）或 pythonw -m voicecontrol.tray_app
开机自启          托盘菜单开关（HKCU Run）
```

典型生产流程：

```text
托盘常驻 → openWakeWord 听到 "hey jarvis" → 蜂鸣提示
→ 录命令（VAD 自动停）→ 转写 → 发送到 Codex
托盘菜单：暂停/恢复 · 开关开机自启 · 退出
```

运行命令（PowerShell）：

```powershell
.venv\Scripts\python.exe -m voicecontrol.main --wake     # 前台调试
.venv\Scripts\pythonw.exe -m voicecontrol.tray_app        # 无控制台托盘后台
```

---

## 4. 仓库结构

按需懒创建文件 — 不要提前搭建空模块脚手架。

采用 src-layout：可导入包 `voicecontrol` 位于 `src/` 下（`pip install -e .` 后生效）；
一律用绝对导入 `voicecontrol.*`，不要用 `src.*`。

```text
VoiceControl/
├── .venv/
├── audio_files/        recordings/  temp/  samples/   （调试音频，git 忽略）
├── logs/               voicecontrol.log（托盘日志，git 忽略）
├── pyproject.toml      包定义（src-layout，含 console script）
├── src/voicecontrol/
│   ├── main.py                 CLI 入口：--once / --vad / --wake / --no-send
│   ├── tray_app.py             无控制台系统托盘常驻
│   ├── audio/                  device_manager, recorder（StreamRecorder, MicFrameStream）
│   ├── stt/                    whisper_engine
│   ├── wake_word/              detector（openWakeWord）
│   ├── vad/                    silero_vad（增量端点检测）
│   ├── executor/               app_driver（基类）, codex_driver, window_utils
│   ├── pipeline/               orchestrator
│   ├── config/                 settings
│   └── utils/                  feedback（蜂鸣）, autostart（HKCU Run 开关）
├── requirements.txt
├── README.md
├── README_EN.md
├── AGENTS.md
└── AGENTS_CN.md
```

模块边界（职责分离）：

- `audio/` — 列出设备、录音、保存/播放 WAV、校验。不含 STT/VAD/唤醒词逻辑。
- `stt/` — 加载模型、转写文件/数组、规范化结果。不含麦克风逻辑。
- `executor/` — 聚焦窗口、发送文本、模拟输入。不含 STT/录音逻辑。
- `pipeline/` — 编排各切片；调用下层模块，不重复实现。
- `config/` — 所有可调参数集中于此；其它地方不硬编码路径/参数。
- `utils/` — 仅放无处归属的代码。

---

## 5. 关键默认值（config）

```python
SAMPLE_RATE = 16000
CHANNELS = 1
WHISPER_MODEL_SIZE = "small"
WHISPER_DEVICE = "cuda"          # 兜底 "cpu"
WHISPER_COMPUTE_TYPE = "float16" # 兜底 "int8"
VAD_SILENCE_DURATION = 3.0
WAKE_WORD_MODEL = "hey_jarvis"
CODEX_WINDOW_TITLE = "Codex"
```

STT 模块至少需支持：

```python
def transcribe_file(path: str | Path) -> str: ...
# 后续: def transcribe_array(audio: np.ndarray, sample_rate: int) -> str: ...
```

---

## 6. Executor 设计

计划对接多个目标应用，因此使用轻量驱动抽象（这是有依据的抽象，并非过度设计）。

```python
class AppDriver:
    """每个目标应用一个驱动（Codex、ChatGPT、Cursor、...）。"""
    def focus(self) -> None: ...
    def send_prompt(self, text: str) -> None: ...   # 优先剪贴板粘贴 + Enter
```

规则：

- 先实现 Codex Desktop；其它应用后续以驱动形式添加。
- 优先**剪贴板粘贴**，而非逐字输入（中文 / 长提示词）。
- 每次桌面操作前后加短延迟并打清晰日志。
- 注意：Alt+Tab 不稳定、输入法问题、焦点丢失、管理员权限边界、编辑器截获热键。

按需使用的工具：`pyperclip`、`pywin32`、`keyboard`。

---

## 7. 编码规范

- 简单、可读的 Python；小函数；显式优于取巧。
- 公开函数/方法尽量加类型注解。
- 路径用 `pathlib.Path`。除 `config/` 外不硬编码路径。
- 可复用模块用 `logging`；`print` 仅用于 CLI 入口和 `__main__` 调试块。
- 命名：`snake_case` 文件/函数/变量/模块，`PascalCase` 类，`UPPER_CASE` 常量。
- 除非明确需要，避免全局可变状态。

---

## 8. 错误处理

显式处理 Windows 失败场景 — 切勿静默吞掉：

```text
麦克风不可用 · 无效设备索引 · 音频文件缺失
模型加载失败 · 转写结果为空 · 窗口未找到
权限被拒绝 · 热键冲突
```

可复用模块：抛出清晰异常或记录日志。CLI 入口：打印错误即可。

音频规则：始终支持手动测试；尽早保存调试 WAV；优雅处理麦克风缺失；不要假设默认设备正确；提供设备列表函数。

---

## 9. 依赖管理

所有运行时依赖在 `requirements.txt` 中，并与 `pyproject.toml` 同步。
有意添加：说明原因、优先稳定/常用包、不重复。

---

## 10. 超出 MVP 范围（后续计划）

```text
TTS · Obsidian · Computer Use · LLM 路由 · 多 Agent
GUI/设置界面 · 安装包
真正的 Windows Service（Session 0 无法驱动桌面 — 用托盘应用）
ChatGPT/Cursor 驱动（计划以新 AppDriver 子类形式添加）
```

---

## 11. Agent 行为准则

1. 先读 `README.md` 和本文件；创建文件前先查看目录结构。
2. 做最小有用改动；每一步都保持代码可运行。
3. 一个可运行的垂直切片，胜过许多半成品模块。
4. 保持命名约定；不重写无关文件。
5. 给出用户应运行的确切 PowerShell 命令。
6. 对不确定的 Windows 音频行为，先写诊断脚本。

开发哲学：**先跑起来 → 可观测 → 稳定 → 快速 → 智能。**
