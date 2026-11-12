# Automatic worker discovery, configuration, and routing preflight

**Goal:** Make the root head agent automatically find or establish the cheapest viable worker route, where the running host allows it. The user should not have to preconfigure worker models just to benefit from this skill. This checklist describes an agent behavior, not a universal configuration API.

## Observe before spending quota

1. Inspect available spawn, messaging, resume, model/effort-selection, worker-definition, permission, and isolation capabilities from the host's advertised tools and accessible local configuration. Check project-level guidance and permissions.
2. Identify the effective head model if exposed, available worker models, allowed reasoning efforts, relative price/quota signals (if reported), and whether worker calls inherit head settings. Avoid probing multiple paid model calls solely to identify availability.
3. Determine which configuration levels exist: **per-spawn**, **session temporary**, **project persistent**, **user/global persistent**, or **none**. Prefer the first two for safety and to avoid unintended future costs.
4. Determine if workers can access mandatory project rules and relevant skills, and if worker delegation can be disabled at the host level. Do not assume the worker's context matches the head's.

## Set up automatically in preference order

| Priority | Capability | Head action |
| --- | --- | --- |
| 1 | Per-call worker model/effort selection | Specify the lowest capable model/effort on each worker spawn; avoid altering persistent settings |
| 2 | Temporary worker/session configuration | Create or select a session-scoped cheap worker role and use it for appropriate tasks |
| 3 | Persistent configuration edits | Only if the user/project explicitly authorizes them and host policy allows; make minimal reversible changes, preserve settings, and handle restart requirements |
| 4 | No supported way to select cheaper workers | Use D0/direct head execution, or delegate only for non-cost benefits; mention limitations once |

**Do not confuse discovery with setup.** Discovering that a cheap model *could* exist does not configure it. Attempt safe automatic selection/creation before concluding that no cheap route is configured. Never hardcode model names, config file paths, provider-specific commands, prices, or defaults into the skill.

**Never change the head model on the user's behalf** or modify credentials, global preferences, or a different project's settings simply to create a worker. Do not use unrelated shell commands or undocumented controls to bypass permission restrictions. If the environment requires an explicit approval, request it only if the change is necessary; otherwise work with the existing environment.

## Verify the outcome

- Check the actual model/effort parameters submitted to the spawn tool or host-confirmed effective worker routing. Where supported, inspect effective worker metadata after spawn.
- Distinguish **requested model** from **effective model**. A role name, text instruction, config comment, or a worker's own statement does not prove which model ran.
- If the host requires a reload/restart to apply new configuration, do not report the change as effective before it takes effect.
- Classify and retain routing evidence once per environment, refreshing it only when changed:

| Status | Evidence and action |
| --- | --- |
| `VERIFIED_CHEAPER` | Route and actual cost/quota advantage supported by reliable evidence; delegate if total expected cost justifies it |
| `PROVISIONAL_CHEAPER` | Lower-tier model route can be selected, but price or quota impact is unknown; delegate bounded low-risk tasks cautiously, with no savings claim |
| `SAME_TIER` | Worker is known to inherit or use the head's cost tier; prefer D0/head unless another benefit offsets overhead |
| `UNVERIFIED` | Effective worker route cannot be established; do not delegate solely for savings |
| `UNAVAILABLE` | No usable worker spawn; execute directly |

Use only evidence actually exposed by the host. Subscription quota, token count, API price, and time are **different metrics**; they may not track each other. Prefer total expected successful-task usage to a single-call estimate, including startup, context, retries, and head reviews.

## Route-selection checklist for each work packet

1. Can D0 complete the work safely and deterministically?
2. Is direct head execution cheaper than composing, spawning, reviewing, and possibly correcting a worker?
3. If delegating, what is the smallest capable executor? Has the head already specified all essential design decisions?
4. Can the host route to it *now*? If not, can the head establish a session-scoped route without approval?
5. Can the worker receive the applicable project rules/skills and be prevented from nested delegation?
6. Is task verification cheap and objective? Is risk of retry lower than choosing the next capable tier?
7. Is parallelism genuinely useful, or will it create merge conflicts and extra head reviews?

Keep preflight checks lightweight; do not repeat them in every worker prompt. If the host supports neither configuration nor cheaper routing, a **truthful fallback is correct behavior**, not a failure of the skill.

## Reporting routing limitations

When relevant, state one concise fact, not repeated warnings:

- "I selected a cheaper worker model for this task; its quota impact is not exposed by the host."
- "This environment currently routes workers at the same tier as the head and provides no permitted override, so I am using direct execution for cost-sensitive steps."
- "The host requires approval or a restart before a persistent worker configuration change can take effect. I am continuing with the available route."

Do not claim an automatic configuration change occurred unless it actually did.
