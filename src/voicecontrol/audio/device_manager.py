"""Audio input device discovery and validation.

List devices, pick/validate an input device. No recording, STT, VAD, or
wake-word logic here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import sounddevice as sd

from voicecontrol.config import settings

logger = logging.getLogger(__name__)


class DeviceError(RuntimeError):
    """Raised when no usable input device exists or an index is invalid."""


@dataclass(frozen=True)
class InputDevice:
    """A lightweight view of a sounddevice input device."""

    index: int
    name: str
    max_input_channels: int
    default_samplerate: float
    is_default: bool


def list_input_devices() -> list[InputDevice]:
    """Return all devices that can capture audio (>= 1 input channel)."""
    try:
        devices = sd.query_devices()
    except Exception as exc:  # sounddevice / PortAudio failure
        raise DeviceError(f"Failed to query audio devices: {exc}") from exc

    try:
        default_input_index = sd.default.device[0]
    except (TypeError, IndexError):
        default_input_index = None

    result: list[InputDevice] = []
    for index, dev in enumerate(devices):
        if dev["max_input_channels"] < 1:
            continue
        result.append(
            InputDevice(
                index=index,
                name=dev["name"],
                max_input_channels=dev["max_input_channels"],
                default_samplerate=dev["default_samplerate"],
                is_default=(index == default_input_index),
            )
        )
    return result


def get_default_input_device() -> InputDevice:
    """Return the system default input device, or the first available one."""
    devices = list_input_devices()
    if not devices:
        raise DeviceError("No audio input device found. Is a microphone connected?")

    for device in devices:
        if device.is_default:
            return device
    return devices[0]


def validate_device(index: int | None) -> InputDevice:
    """Validate a configured device index.

    ``None`` means "use the default device" (see ``settings.INPUT_DEVICE``).
    """
    if index is None:
        return get_default_input_device()

    for device in list_input_devices():
        if device.index == index:
            return device
    raise DeviceError(
        f"Configured INPUT_DEVICE={index} is not a valid input device. "
        f"Run this module to list available devices."
    )


def print_input_devices() -> None:
    """Human-friendly dump of available input devices (debug helper)."""
    devices = list_input_devices()
    if not devices:
        print("No audio input device found. Is a microphone connected?")
        return

    print(f"Found {len(devices)} input device(s):\n")
    for device in devices:
        marker = " (default)" if device.is_default else ""
        print(
            f"  [{device.index}] {device.name}{marker}\n"
            f"        channels={device.max_input_channels}, "
            f"samplerate={device.default_samplerate:.0f} Hz"
        )

    configured = settings.INPUT_DEVICE
    print(
        f"\nsettings.INPUT_DEVICE = {configured} "
        f"({'default device' if configured is None else 'explicit index'})"
    )


if __name__ == "__main__":
    print_input_devices()
