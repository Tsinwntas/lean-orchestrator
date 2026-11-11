# Runtime capability and model-routing preflight

This is a **runtime decision checklist**, not an installation script or a promise that low-cost models are available. Apply before dispatching expensive work; reuse known results within the same session.

## Observe

1. Identify which host is running the skill, and which tools can actually spawn, message, wait for, or resume workers. If none, set `UNAVAILABLE`.
2. Inspect registered workers (host tool descriptions, configuration, or permitted filesystem reads). Is there an explicit model/effort route? If it inherits the head model, set `SAME_TIER`.
3. Confirm that the requested model is available to the account/session and that the host applies it to **this worker**, not merely to the head. If the binding is opaque, set `UNVERIFIED`.
4. Decide whether the route is *actually lower cost or lower quota impact* than the head, using reliable provider/runtime evidence if available. A smaller name, a `low` reasoning label, or a configuration comment is not proof. If the route and savings are sufficiently verified, set `VERIFIED_CHEAPER`.
5. Check task-specific requirements: worker skills/project rules are reachable, worker cannot recursively delegate when possible, and files have safe write boundaries. Report non-enforced restrictions honestly.

## Status and action

| Status | Evidence | Default behavior |
| --- | --- | --- |
| `VERIFIED_CHEAPER` | Host confirms selected lower-cost worker route | Delegate bounded tasks when estimated overall cost merits it |
| `SAME_TIER` | Explicit inheritance/same head model | Prefer head/D0; delegate for clear parallelism or isolation benefits |
| `UNVERIFIED` | Worker model, availability or price/quotas cannot be established | Do not promise savings; avoid delegation solely to save quota |
| `UNAVAILABLE` | No spawn tool/worker access | Execute directly; say no subagents were used |

**If no cheap worker is configured, do not stop the user's entire request.** Explain the specific missing capability using only details observed in the current host. Avoid mentioning provider names or configuration paths unless those are actually relevant to the runtime. Example messages:

- **No spawn capability:** "This environment does not expose subagent creation. I will perform the task directly and will not claim worker delegation."
- **Same model tier:** "Workers appear to inherit the head model. I can still delegate for isolation or parallelism, but will not assume delegation saves quota."
- **Unverified route:** "I cannot confirm that workers use a lower-cost model. I will prefer deterministic tools and direct execution unless delegation has another clear benefit."
- **Missing project guidance:** "The worker cannot access the required project skill/instructions. I will supply a verified excerpt or keep the implementation with the head."

For any supported host, instruct the user only on configuration controls and paths that are actually documented or available in that host. Never present a provider-specific sample as a universal requirement.

Do not edit user-owned configuration without consent. No vendor-specific configuration is part of this skill; infer capabilities from the running environment rather than assuming a named product.
