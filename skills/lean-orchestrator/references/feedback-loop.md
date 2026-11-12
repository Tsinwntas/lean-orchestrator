<!-- lean-orchestrator-release: 1.7.0 -->
# Feedback, acceptance, and recovery

<a id="states"></a>
## Head-owned states

| State | Meaning / exit condition |
| --- | --- |
| `PLANNED` | Scope, dependencies, and checks are being settled. |
| `READY` | Inputs are current, prerequisites accepted and available, route/budget selected. |
| `RUNNING` | One identified worker/round owns the assigned write scope. |
| `REVIEW` | Result collected; no acceptance implied by `DONE`. |
| `REWORK` | Head prescribed a localized correction within remaining budget. |
| `ACCEPTED` | Head verified the contract against current, integrated/accessible artifacts. |
| `STALE` | Relevant prerequisite/input changed; recheck or replan before reuse. |
| `BLOCKED` | Missing permission, input, safe execution path, or required verification. |
| `FAILED` | Attempt failed; diagnose and replan/direct-execute or report the gap. |
| `CANCELLED` | Stop confirmed or workspace isolated from any still-running attempt. |

`REPLAN` is a head decision: change the plan, invalidate affected descendants, preserve useful verified artifacts, and return appropriate tasks to `PLANNED`. `BLOCK` is a decision that sets `BLOCKED`. Never mark a task cancelled just because a cancellation request was sent. Keep an uncertain still-running worker visible in the ledger and protect its write scope.

<a id="example"></a>
## A0 → A1 → correction

Illustrative task: prepare a simple dataset and a short summary. The head chooses an authorized economical route, specifies the output contract, and assigns a bounded transformation. Worker routing is selected through host controls, not through this text.

<!-- packet: example-task -->
```text
ROLE: WORKER
TASK ID: A0
ROUND: 1
GOAL: Write normalized.csv with columns name,score, preserving row order.
DEPENDS ON: NONE
BASE: The literal source below is the complete immutable input for this assignment.
WORKSPACE: The isolated work directory provided by the host for A0.
READ SCOPE: Literal CSV: name,score / " Ada ",3 / "Ben",4. Slashes separate lines.
WRITE SCOPE: normalized.csv only.
GUIDANCE: No additional project rules apply to this isolated example.
SKILLS: NONE
PROCEDURE:
  1. Parse the supplied two-row CSV; trim leading/trailing spaces from names.
  2. Write a header and two rows to normalized.csv; preserve integer scores/order.
CONSTRAINTS:
  No delegation, redesign, unrelated writes, network access, or external actions.
LIMITS: At most 4 tool calls and 1 local repair; report within 120 words.
VERIFY: Header name,score; rows Ada,3 then Ben,4; exactly two data rows.
DELIVER: normalized.csv in this workspace and a concise report.
STOP IF: Input interpretation is ambiguous, writing is unavailable, or limits are reached.
```

The head inspects the actual CSV, confirms the values and row count with a deterministic check, and transfers it to the next worker's workspace if required. Only then does the head accept A0. A1 receives a complete packet to write a summary with **row count and total score**, using this accepted snapshot; its verification requires both 2 and 7. Suppose the worker omits the total despite reporting `DONE`.

| Interaction | Decision |
| --- | --- |
| Worker A0 returns the normalized data | Head checks and accepts A0. |
| Head dispatches A1 with accepted data and explicit summary requirements | A1 runs only after prerequisites are available. |
| Worker A1 reports `DONE`; summary omits total score | Head chooses `REWORK`, not acceptance based on status. |
| Head sends A1 round 2 with exact missing requirement and current base | Reuse the session only if context and route remain suitable. |
| Worker returns corrected summary | Head verifies row count 2 and total 7, then accepts A1. |
| Head checks both final files against the user's request | Deliver artifacts and actual verification. |

The numbers are from this example's literal data, not measured model-performance results. An ordinary D0 tool could complete this tiny task more cheaply; the example illustrates communication, **not a recommendation to delegate trivial work**. In real use, choose packets large enough to justify coordination.

<a id="edge-cases"></a>
## Recovery decisions

| Event | Required head action |
| --- | --- |
| Host offers cheap per-call routing but no worker role exists | Select the permitted route directly; do not ask the user to create a role first. |
| Host confirms a model but exposes only API price, not quota | Keep route confidence and quota-cost uncertainty separate. |
| Worker sees Lean Orchestrator in its skill catalog | It remains a worker; skill visibility grants no delegation authority. |
| Mandatory implementation skill is absent | Provide authorized complete requirements or move work to a capable route/head. |
| Tests pass but artifacts violate the contract | Reject/rework; tests are evidence, not the definition of success. |
| Worker alters acceptance tests to hide a failure | Reject, preserve evidence, restore only its unauthorized changes safely, replan. |
| Old round completes after a newer result | Quarantine the stale result; do not overwrite accepted work. |
| Worker times out and cancellation is unconfirmed | Do not hand its write scope to another worker; isolate or block. |
| A0's accepted output changes while A1 is running | Stop affected work where possible; mark A1 stale and revalidate its inputs/results. |
| Repeated failure exhausts the finite budget | Diagnose/replan or take over; do not reset attempt counts through renamed tasks. |
| Head resumes after context loss | Reconcile worker handles, input versions, partial writes, and accepted artifacts before dispatch. |
| Required check cannot run | Record unverified status; use a justified alternative or block acceptance. |
| User changes goal or cancels | Stop obsolete work, preserve user edits, account for active workers and partial artifacts. |

For independent work, gather concise reports and checks at a single review checkpoint when economical. Do not repeatedly wake the head to ask whether a worker is finished. If the host is synchronous, a normal tool return is the report; if it cannot resume a worker, send a new complete correction assignment. Never invent an asynchronous messaging system.
