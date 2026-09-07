"""Order reconciliation.

The re-entry is not visible at any single call site. Read top to bottom it is
handler -> save -> hook -> emit -> handler, three layers apart:

    on_order_updated()  ->  save_order()
    save_order()        ->  AFTER_SAVE hook (persistence layer)
    after_save()        ->  BUS.emit("order.updated")
    BUS.emit(...)       ->  on_order_updated()

Nothing bounds the depth and nothing makes the write idempotent, so a single
update re-enters its own handler until the interpreter's stack runs out. No
single file shows the loop: the handler, the persistence layer, and the ORM
callback each look reasonable on their own.
"""

from __future__ import annotations

from collections import defaultdict

STORE: dict = {}
AFTER_SAVE: list = []


class Bus:
    """Minimal in-process event bus."""

    def __init__(self) -> None:
        self.handlers = defaultdict(list)

    def on(self, topic: str):
        def register(fn):
            self.handlers[topic].append(fn)
            return fn

        return register

    def emit(self, topic: str, payload: dict) -> None:
        for handler in self.handlers[topic]:
            handler(payload)


BUS = Bus()


def save_order(order: dict) -> dict:
    """Persistence layer. Writes the row, then runs the ORM-style hooks."""
    STORE[order["id"]] = dict(order)
    for hook in AFTER_SAVE:
        hook(order)
    return order


def after_save(order: dict) -> None:
    """ORM callback. Announces the write so read models can catch up."""
    # COVERT-RECURSION: the hook that runs *because of* a write publishes the
    # event that triggers the next write. The cycle closes here.
    BUS.emit("order.updated", order)


AFTER_SAVE.append(after_save)


@BUS.on("order.updated")
def on_order_updated(order: dict) -> None:
    """Recompute the denormalised total and persist it.

    COVERT-RECURSION: no depth bound, no visited set, no version check, no
    "did anything actually change?" guard. save_order() re-enters this handler
    through after_save().
    """
    total = sum(line["qty"] * line["unit_price"] for line in order["lines"])
    order["total"] = total
    save_order(order)


def reconcile(order: dict) -> dict:
    save_order(order)
    return STORE[order["id"]]


if __name__ == "__main__":
    # Raises RecursionError: reconcile() never returns.
    print(reconcile({"id": "o-1", "lines": [{"qty": 2, "unit_price": 5}]}))
