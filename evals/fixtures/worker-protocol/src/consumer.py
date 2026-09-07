"""Queue consumer.

The broker delivers at-least-once. Its lease protocol is, in order:

    lease = receive()      # message becomes invisible for visibility_timeout
    renew(lease)           # while the handler still runs past that timeout
    ack(lease)             # on success -- deletes the message
    nack(lease)            # on failure -- returns it for immediate redelivery

Only the two endpoints are wired below. The happy path prints "ok" and the
row lands in the store, so a demo run looks correct.
"""

import queue

JOBS: "queue.Queue" = queue.Queue()


class Lease:
    def __init__(self, payload):
        self.payload = payload


class Broker:
    """Stand-in for the broker SDK. All four methods exist."""

    def receive(self) -> Lease:
        return Lease(JOBS.get())

    def renew(self, lease: Lease) -> None:
        pass

    def ack(self, lease: Lease) -> None:
        pass

    def nack(self, lease: Lease) -> None:
        pass


def run(broker: Broker, store) -> None:
    while True:
        lease = broker.receive()
        store.write(lease.payload)
        print("ok")


if __name__ == "__main__":
    run(Broker(), None)
