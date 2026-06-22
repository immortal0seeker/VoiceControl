"""Asset paths for the PySide6 UI."""

from __future__ import annotations

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def asset_path(name: str) -> Path:
    """Return the absolute path to a UI asset."""
    return ASSETS_DIR / name
