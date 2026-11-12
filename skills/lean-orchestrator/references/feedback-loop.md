# Worked loop: auto-routing, dependent tasks, and targeted rework

**User:** Add an account-settings endpoint and tests, omitting secrets and handling a missing account.

The root head first checks whether the host permits a lower-cost worker route. It selects a cheaper worker directly if available, otherwise establishes a permitted temporary worker route, verifies the effective route when possible, or falls back honestly. **The user is not expected to preconfigure worker models.** The head also identifies required project skills and passes them into each worker's context.

| Step | Interaction | Head decision |
| --- | --- | --- |
| 0 | Head inspects tools/model routing, skills, and requirements | Auto-select/configure cheaper worker if permitted; settle API contract |
| 1 | Head → Worker 0: `A0` endpoint implementation with fixed response contract | DISPATCH; allow only specified source file |
| 2 | Worker 0 → Head: `A0 DONE` with changed file and observed check | Head independently inspects diff and ACCEPTS A0 |
| 3 | Head → Worker 1: `A1` tests for present and missing account | DISPATCH only after A0 is accepted |
| 4 | Worker 1 → Head: `A1 DONE`, tests green | Head notices missing secret-redaction assertion; REWORK |
| 5 | Head → Worker 1: `A1 ROUND 2`, precise missing assertion | Resume if economical, otherwise send bounded correction to new worker |
| 6 | Worker 1 → Head: `A1 ROUND 2 DONE` with new assertion | Head verifies and ACCEPTS A1 |
| 7 | Head / D0: `A2` affected tests and integration check | ACCEPT or repair |
| 8 | Head → User: deliver finished files and actual verification | Report route as verified, provisional, or unavailable |

Example correction:

```text
ROLE: WORKER (NEVER HEAD)
TASK ID: A1
ROUND: 2
PRIOR RESULT: Test code did not assert API_TOKEN is omitted from the JSON response.
GOAL: Add the missing assertion to the existing-account test.
WRITE SCOPE: tests/test_settings.py only
PROCEDURE:
  1. Reuse the existing response object.
  2. Assert API_TOKEN is absent from the serialized response.
  3. Run: python -m pytest tests/test_settings.py -q
CONSTRAINTS: No endpoint edits or refactoring. No subdelegation.
VERIFY: Focused test passes; diff contains the assertion.
STOP IF: Fixture cannot expose the value being checked; report the blocker.
```

**No unnecessary head wake-ups:** The head can group routine independent checks into one meaningful review checkpoint, but it cannot release dependent work without accepting prerequisites. The goal is low total head+worker usage, not maximizing the number of worker reports.

**Parallelism:** An independent read-only documentation audit can run alongside A0. Tasks sharing writable files need serialization or isolated integration.

**No resumable workers:** Treat `A1 ROUND 2` as a new worker call carrying the minimal context. Synchronous tool returns count as worker reports; do not assume persistent messaging or background work.
