# order-sync

Background order reconciler. Consumes order rows from a store and keeps
denormalised totals in sync through an in-process event bus and a persistence
hook. No HTTP server, no users, no client-reachable datastore.
