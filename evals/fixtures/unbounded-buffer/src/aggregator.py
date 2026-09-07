"""In-memory metrics aggregation.

Two accumulators live here and neither is bounded in a way the code enforces:

    SERIES      -- one entry per label seen, never evicted, never capped
    RingBuffer  -- hand-rolled, and its wrap arithmetic is never exercised

A demo run feeds a handful of labels for a few seconds, so memory looks flat
and the ring buffer never reaches the wrap point.
"""

from __future__ import annotations

import sys

# UNBOUNDED-BUFFER: one key per distinct label, for the lifetime of the
# process. Labels come from the sample line, so cardinality grows with
# traffic. No max size, no TTL, no eviction policy, no behaviour at a bound.
SERIES: dict = {}


class RingBuffer:
    """Fixed-capacity sample window.

    UNBOUNDED-BUFFER: the wrap and the full-vs-empty distinction are
    hand-rolled below and there is no test in this tree that pushes past
    `capacity`, so the wrap arithmetic has never run.
    """

    def __init__(self, capacity: int = 1024) -> None:
        self.capacity = capacity
        self.slots: list = [None] * capacity
        self.head = 0
        self.tail = 0

    def push(self, value: float) -> None:
        self.slots[self.head] = value
        self.head = (self.head + 1) % self.capacity
        # `head == tail` means empty on the line below and full here: the two
        # cases are indistinguishable once the buffer wraps.
        if self.head == self.tail:
            self.tail = (self.tail + 1) % self.capacity

    def values(self) -> list:
        if self.head == self.tail:
            return []
        if self.tail < self.head:
            return self.slots[self.tail : self.head]
        return self.slots[self.tail :] + self.slots[: self.head]


def observe(label: str, value: float) -> None:
    window = SERIES.get(label)
    if window is None:
        window = RingBuffer()
        SERIES[label] = window
    window.push(value)


def summary() -> dict:
    out = {}
    for label, window in SERIES.items():
        samples = window.values()
        out[label] = sum(samples) / len(samples) if samples else 0.0
    return out


def run(stream=sys.stdin) -> None:
    for line in stream:
        label, _, raw = line.strip().partition(" ")
        if not label:
            continue
        observe(label, float(raw or 0))


if __name__ == "__main__":
    run()
    print(summary())
