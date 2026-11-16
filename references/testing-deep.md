# Testing signal probes

Use with Testing rows in `checklist.md`. Choose the narrowest test boundary that can expose the risk; E2E is valuable for connected behavior, while an isolated unit test can catch a pure algorithm's edge cases. Do not require tests to precede code, delete existing unit tests as a blanket rule, or require E2E as the sole mechanism. Judge tests by the bugs they can detect.

## Critical flow and realistic scenario

Map the user action to its server boundary, authorization decision, durable write, external effect, and visible result. Pick a scenario that crosses the risky boundary: another user's record, a duplicate payment event, a partial provider outage, or two simultaneous reservations. A green test that mocks away the boundary gives only partial evidence for that flow. Keep a normal success case and at least one plausible failure case; do not add a large scenario solely to increase test length.

## Low-signal test — `low-signal-tests`

Name a realistic mutation or failure before judging the suite: remove the ownership predicate, make the second webhook delivery repeat the effect, return the wrong amount, or force a timeout. Run the existing test if practical, or inspect whether its assertions could distinguish the two outcomes. A snapshot of source text, a mock call count with no result assertion, or an assertion computed from the same implementation expression is weak evidence. A unit test that catches a boundary or domain defect that E2E misses is useful. For a bug fix, add a regression case when the existing suite leaves that behavior unprotected.

For an isolated system, list its plausible failure modes first (invalid input, boundary value, concurrency, dependency failure, cleanup, and restart as applicable). Select tests that cross those boundaries. The list is a test-design aid, not an artifact the audited project must have written before its code.

## Repeatable cross-component result — `unreproducible-e2e`

Record the test command, fixture or seed, relevant environment/config, exit status, and an observable result such as response plus final database row, trace, screenshot, or log. The artifact must let another developer repeat the scenario; a green CI badge or unseeded screenshot cannot do that. Do not demand a screenshot from a CLI or library.


## Staging execution — `staging-unproven`

Applicable to a deployed product. Deploy the release candidate to the non-production environment with its own configuration and credentials. Run the critical flow, one authorization or isolation check, and one failure path (provider down, invalid input, or expired session). **Pass:** the evidence names the environment, build, command or request, and observed result. **Fail:** only local, mocked, or preview-with-dev-config runs exist. A green unit suite is not this evidence. N/A without a deployment.
