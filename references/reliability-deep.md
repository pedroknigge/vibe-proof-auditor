# Reliability and recovery probes

Use with the applicable Testing, Architecture, Error handling, Performance, and Process rows in `checklist.md`. Each probe describes an observable failure. Read the implementation and run only against fixtures, a local server, or disposable data. Do not invoke a production endpoint or restore production data to discover whether a control works. A search hit locates a candidate; a missing hit is not proof.

## Concurrent invariant break — `concurrent-invariant-break`

Applicable when multiple requests or workers can change the same balance, stock, quota, unique reservation, or versioned record. Find the read → decision → write sequence. Seed the smallest state that permits one operation. Start two operations at a barrier and release them together. **Pass:** one wins or both resolve to a valid serial order, and the final state satisfies the invariant. **Fail:** both report success and leave a negative balance, oversell, duplicate reservation, or lost update. A database constraint, compare-and-swap, lock, or transaction may provide the guarantee; do not require one named pattern. Record the setup, two results, and final row.

## Repeated effect — `duplicate-effect`

Applicable to payments, grants, emails, webhooks, job deliveries, and other effects that may be retried. Replay the same logical operation or provider event twice with the same identity. **Pass:** the business rule deliberately permits both effects, or the second attempt returns/reuses the first outcome without repeating the effect. **Fail:** one payment intent, event, or request causes two charges, grants, or messages. Check idempotency storage, uniqueness, and retention long enough for the provider's retry window; a client-side disabled button is not a control.

## Split durable write and external effect — `split-write-loss`

Applicable when a request writes a database row and then publishes a message, calls a provider, or starts a job. Identify the crash point between the two actions and inject a failure there. **Pass:** recovery can determine which work remains and deliver or reconcile it without duplicating a non-idempotent effect. **Fail:** the row says complete while its required effect is permanently absent, or the effect occurred while the row says it did not. An outbox, transactional broker, idempotent consumer plus reconciliation, or another proven design can work. Cite the failure point and recovery test.

## Bounded remote calls and retries — `unsafe-retry` / `retry-storm`

Applicable to remote dependencies and workers that retry. Force timeout, 429/5xx, and permanent rejection. Inspect total deadline, which errors retry, attempt bound, backoff, and terminal state. **Fail:** a request waits indefinitely, retries a non-idempotent charge, or a poisoned job loops and amplifies provider load. A circuit breaker is useful in some systems but is not required to Pass. Record attempt count and final state rather than the mere presence of retry code.

## Critical cache freshness — `stale-critical-cache`

Applicable when cached values influence authorization, price, inventory, or quota. Populate the cache, then revoke access or update the value in the authoritative store. Exercise the same read/write path while the old cache entry exists. **Pass:** invalidation, versioning, or expiry prevents the stale value from authorizing an invalid action. **Fail:** a revoked user still acts, or an outdated value controls a money or stock decision. A stale display label alone is not this finding.

## Migration, rollback, and restore — `rollback-trap` / `migration-rollback-break` / `rollback-unproven` / `restore-unproven`

Applicable to deployed systems and durable data. Seed a nonempty disposable database with representative old rows. Run the migration and the new application path; then run the previous application version against the migrated state. **Pass:** the previous version can still serve the critical flow, or a tested restore/reconciliation returns a valid state within the product's recovery expectation. **Fail:** code redeploy succeeds but the old reader or writer crashes, or changed data is silently lost. For backup claims, restore into a separate disposable database and compare key counts, referential integrity, and a critical read; the existence of a snapshot is not proof it restores. Capture commands, exit codes, and recovery time. The `evals/fixtures/rollback-trap` tree demonstrates a schema rename that breaks the previous reader.

## Resource lifecycle and protocol completeness

For resource acquisition, force an early return and an exception between acquire and release; inspect the open handle or connection count afterward. For a protocol or state machine, derive the required transitions from its actual API contract and exercise timeout, retry, cancellation, and duplicate delivery. A `finally` or `ack()` text match is only a lead; the observed state determines the mark. See `resource-leak`, `cleanup-on-failure-missing`, and `step-skipped` in `checklist.md`.
