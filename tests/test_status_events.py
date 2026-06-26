from __future__ import annotations

import unittest

from voicecontrol.events.status import StatusEvent, StatusType, StatusPublisher


class StatusPublisherTests(unittest.TestCase):
    def test_publish_notifies_subscribers_with_status_event(self) -> None:
        received: list[StatusEvent] = []
        publisher = StatusPublisher()

        publisher.subscribe(received.append)
        event = publisher.publish(StatusType.LISTENING, message="ready")

        self.assertEqual(received, [event])
        self.assertEqual(event.type, StatusType.LISTENING)
        self.assertEqual(event.message, "ready")

    def test_unsubscribe_removes_subscriber(self) -> None:
        received: list[StatusEvent] = []
        publisher = StatusPublisher()

        unsubscribe = publisher.subscribe(received.append)
        unsubscribe()
        publisher.publish(StatusType.WAKE)

        self.assertEqual(received, [])

    def test_subscriber_error_does_not_block_other_subscribers(self) -> None:
        received: list[StatusEvent] = []
        publisher = StatusPublisher()

        def broken(_event: StatusEvent) -> None:
            raise RuntimeError("subscriber failed")

        publisher.subscribe(broken)
        publisher.subscribe(received.append)

        with self.assertLogs("voicecontrol.events.status", level="ERROR"):
            publisher.publish(StatusType.ERROR, message="boom")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].type, StatusType.ERROR)


if __name__ == "__main__":
    unittest.main()
