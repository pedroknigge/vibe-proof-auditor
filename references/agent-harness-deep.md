# Agent harness probes

Use only when the audited product assembles model requests, manages tools/context, compacts history, or dispatches agents. A project that merely calls an LLM endpoint for one feature is not automatically an agent harness. Apply the two harness-specific Performance rows in `checklist.md` only to surfaces the project owns.

## Cost per completed task — `harness-cost-unmeasured`

Trace one representative task across its full run, including retries and child agents. From provider usage and prices, separate output, uncached input, and cached input; record cache hits, turns, latency, tool errors, and task outcome. Compare the same task mix before and after a proposed change. A lower token count for one request, with extra turns or a worse completion rate, does not prove lower cost per completed task. If the app makes no cost or efficiency claim and telemetry cannot be observed, use `insufficient evidence` for an inaccessible provider log rather than inventing a Fail.

## Rendered request and context — `harness-context-waste`

Inspect actual serialized requests, not only prompt templates. Look for volatile timestamps or IDs before a cache boundary, nondeterministic tool order, repeated instructions, and tools whose full schemas ride along even when unused. Check the provider's current cache contract (including minimum length and TTL) before claiming a cache miss. For large tool output, verify whether full data remains searchable by path or retrieval; a short inline tail with the full output saved can preserve evidence, while silent truncation can lose it. Test prompt edits, schema offloading, and compaction against task success as well as cost. Model routing and agent count are design proposals until a task-level comparison supports them; do not demand a particular model mix.

