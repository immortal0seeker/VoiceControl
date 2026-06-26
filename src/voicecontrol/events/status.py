"""Lightweight status events shared by pipeline, UI, tray, and TTS."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class StatusType(StrEnum):
    """Known runtime states emitted by the voice pipeline."""

    LISTENING = "listening"
    WAKE = "wake"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    SENDING = "sending"
    DONE = "done"
    ERROR = "error"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass(frozen=True)
class StatusEvent:
    """One status transition or notification."""

    type: StatusType
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


StatusSubscriber = Callable[[StatusEvent], None]
Unsubscribe = Callable[[], None]


class StatusPublisher:
    """Synchronous in-process status event publisher."""

    def __init__(self) -> None:
        self._subscribers: list[StatusSubscriber] = []

    def subscribe(self, subscriber: StatusSubscriber) -> Unsubscribe:
        """Register ``subscriber`` and return a function that removes it."""
        self._subscribers.append(subscriber)

        def unsubscribe() -> None:
            try:
                self._subscribers.remove(subscriber)
            except ValueError:
                pass

        return unsubscribe

    def publish(
        self,
        event_type: StatusType,
        message: str = "",
        data: dict[str, Any] | None = None,
    ) -> StatusEvent:
        """Publish a status event to current subscribers."""
        event = StatusEvent(type=event_type, message=message, data=data or {})
        for subscriber in list(self._subscribers):
            try:
                subscriber(event)
            except Exception:
                logger.exception("Status subscriber failed for %s.", event.type)
        return event


default_status_publisher = StatusPublisher()


def subscribe(subscriber: StatusSubscriber) -> Unsubscribe:
    """Subscribe to the process-wide default status publisher."""
    return default_status_publisher.subscribe(subscriber)


def publish(
    event_type: StatusType,
    message: str = "",
    data: dict[str, Any] | None = None,
) -> StatusEvent:
    """Publish on the process-wide default status publisher."""
    return default_status_publisher.publish(event_type, message=message, data=data)
