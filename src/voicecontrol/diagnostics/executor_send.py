"""Executor send diagnostics."""

from __future__ import annotations

from pathlib import Path

from voicecontrol.diagnostics.store import DiagnosticResult, append_diagnostic_result
from voicecontrol.executor.router import create_driver_from_config, normalize_target
from voicecontrol.executor.window_utils import WindowError


DEFAULT_TEST_PROMPT = "这是一条来自 VoiceControl 控制中心的测试消息。"


def run_executor_send_test(
    *,
    config: dict,
    target: str | None = None,
    text: str = DEFAULT_TEST_PROMPT,
    auto_enter: bool = False,
    diagnostic_path: str | Path | None = None,
) -> DiagnosticResult:
    """Send a diagnostic prompt to the configured executor target."""
    executor_config = config.get("executor", {})
    selected_target = normalize_target(
        target or str(executor_config.get("default_target", ""))
    )

    try:
        driver = create_driver_from_config(config, selected_target)
        driver.send_prompt(text, auto_enter=auto_enter)
    except (ValueError, WindowError) as exc:
        result = DiagnosticResult(
            name="executor_send",
            status="error",
            details={
                "target": selected_target,
                "auto_enter": auto_enter,
            },
            error=str(exc),
        )
    else:
        result = DiagnosticResult(
            name="executor_send",
            status="ok",
            details={
                "target": selected_target,
                "app_name": driver.app_name,
                "auto_enter": auto_enter,
                "text_length": len(text),
            },
        )

    append_diagnostic_result(result, path=diagnostic_path)
    return result
