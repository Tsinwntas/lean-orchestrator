# Reusable worker task packet

Copy and fill this structure. Supply specifics rather than placeholders to the worker. The head retains the original problem and all design decisions; workers receive only relevant facts.

```text
TASK ID: A1
ROUND: 1
EXECUTOR: L1 (use actual available model/effort if configurable)
GOAL: <one unambiguous, testable result>
DEPENDS ON: A0 (head-ACCEPTED)
INPUTS:
  - <exact path and relevant functions, or supplied snippet>
  - <fixed interface agreed by head>
PROJECT GUIDANCE:
  - <applicable repository, organization, or host instructions and readable paths; or NONE>
REQUIRED SKILLS:
  - <specific relevant project skill names/paths to load, or NONE>
OPTIONAL SKILLS:
  - <additional implementation skills allowed for discovery, or NONE>
WRITE SCOPE:
  - <exact editable paths or READ ONLY>
PROCEDURE:
  1. <exact action>
  2. <exact action>
  3. <exact action>
CONSTRAINTS:
  - <no architecture or unrelated file changes>
  - <act only as worker, not Lean Orchestrator head; do not spawn agents or communicate with user>
  - <follow required project skills; additional implementation skills must stay within scope>
VERIFY:
  - Command: <specific command>
  - Expected: <specific assertion / exit status>
DELIVER:
  - <exact files and compact outcome report>
STOP IF:
  - <missing dependency, non-writable files, unexpected result, unsafe operation>
```

Tell the worker to reply:

```text
TASK ID: A1
ROUND: 1
STATUS: DONE | BLOCKED | FAILED
CHANGED: <paths / NONE>
CHECKS: <commands and observed results / NOT RUN because ...>
SKILLS USED: <required or additional skill names/paths actually applied; or NONE>
ISSUES: <NONE or specific evidence>
```

## Correction packet for the same task

```text
TASK ID: A1
ROUND: 2
PRIOR RESULT: Reported DONE; head review found <precise defect>
GOAL: Fix ONLY <the defect>
INPUTS: <current files and minimal necessary results>
WRITE SCOPE: <same or narrower scope>
PROCEDURE:
  1. <specific expected fix>
  2. <run focused verification>
CONSTRAINTS: Preserve all other behavior. No new designs or refactoring.
VERIFY: <exact check and expected outcome>
STOP IF: <blocked condition>
```

Do not ask the worker to diagnose a broad issue when the head can characterize the failure. If the problem genuinely needs sophisticated reasoning, escalate rather than sending vague corrections to a cheap model.
