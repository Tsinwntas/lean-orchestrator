# Worked example: dependent tasks and targeted rework

**User:** Add an account settings endpoint and a test. The response must redact secrets and handle a missing account.

The head inspects the project layout and settles the API contract; a low-tier worker is not asked to invent it.

| Step | Speaker | Action | Head's decision |
| --- | --- | --- | --- |
| 1 | Head → Worker 0 | `A0`: implement the specified endpoint, in file `settings_routes.py`, with exact response contract | Dispatch |
| 2 | Worker 0 → Head | `A0 DONE`: file changed; syntax check passes | Head reviews diff, accepts A0 |
| 3 | Head → Worker 1 | `A1`: add tests for existing account and missing account in `test_settings.py` | Dispatch after A0 acceptance |
| 4 | Worker 1 → Head | `A1 DONE`: tests reported green | Head reads test code and finds secret-redaction assertion absent |
| 5 | Head → Worker 1 | `A1 ROUND 2`: add *exact* missing redaction assertion; same file; don't change endpoint; run one test | REWORK |
| 6 | Worker 1 → Head | `A1 ROUND 2 DONE`: added assertion; test passes | Head verifies and accepts A1 |
| 7 | Head / D0 | `A2`: run the complete affected test suite | ACCEPT or fix integration defects |
| 8 | Head → User | Report shipped changes, actual tests, and limitations | Deliver |

Example correction message:

```text
TASK ID: A1
ROUND: 2
PRIOR RESULT: You reported success; review found that test_settings.py
  does not assert API_TOKEN is absent from the JSON response.
GOAL: Add that one assertion to the existing-account test.
WRITE SCOPE: tests/test_settings.py only
PROCEDURE:
  1. Reuse the existing response object in the test.
  2. Assert API_TOKEN is absent from the serialized response.
  3. Run: python -m pytest tests/test_settings.py -q
CONSTRAINTS: No endpoint edits, no production refactoring.
VERIFY: Focused test passes; assertion text exists in diff.
STOP IF: Test fixture does not expose this value; report the blocker.
```

The names and commands above are illustrative: a real head must inspect its target project before authoring these packets. For platforms without resumable workers, `A1 ROUND 2` is sent to a fresh worker with the minimal report and diff context.

## Independent tasks

If A0 and a read-only documentation audit have no dependencies or write overlap, the head may run them concurrently. The audit's completion does not imply A0 is accepted or unblock A1.
