<!-- lean-orchestrator-release: 1.9.0 -->
# Routing setup and dispatch gate

Read before the first spawn, including exploration/review workers. Cache capabilities; reuse them while unchanged. Apply the short dispatch gate on every spawn, resume, correction, or route change. These are instructions and bookkeeping fields, not a runtime or literal host API parameters.

<a id="discover"></a>
## Discover without spawning a default worker

Use advertised tools, authorized local configuration, help/schema, and existing roles. Inspect only relevant settings, not credentials or entire accounts. Consult authoritative host documentation only when needed and accessible, matching the installed version.

Establish worker creation, explicit model/effort selection, role precedence, permissions, cancellation/wait/resume, context inheritance, skill/file access, and isolation. Identify eligible models using host availability plus project/user authorization; a general catalog does not establish account access. Record cost evidence for the user's objective separately from model capability. API prices do not establish subscription quota weights.

Compare available workers with the selected head. A documented lower worker tier or evidence supporting lower expected cost may identify an economical candidate even when quota weights are hidden. Model names alone are not a price ranking. Head-model, head-equivalent-tier, and higher-tier workers require explicit user approval, regardless of smaller context or reasoning effort. An authorized worker allowlist or prior scope-specific approval can be reused within its scope.

One bounded inspection pass should normally suffice; further inspection needs a concrete blocker. Do not spawn an unconfigured exploration agent to discover configuration. The head can inspect tools/configuration directly. Record environment/version, model availability, permissions, relevant configuration, and evidence; invalidate affected cached decisions when these change.

<a id="rank"></a>
## Cheapest-capable-first candidate ladder

Before picking a worker for a task, list the eligible available **model + reasoning-effort** combinations, ranked by expected **total** cost for that task: per-model rate or documented quota class where exposed; context, output, tool cost, and likely correction effort where known. Keep subscription quota, API spending, latency, and token count distinct. Where numbers are opaque, use a disclosed **provisional** order from authorized model tiers, actual observed behavior, and available documentation. Never invent a price, infer price from a name alone, or insist on a lengthy investigation to rank trivially different choices.

**The default is the first plausible cheapest capable candidate.** Start with the smallest viable route, not a default mid-tier or the worker used most recently. Match task complexity to the *minimum needed*: precise mechanical or routine edits normally deserve the smallest tool-capable worker; more demanding implementations move upward only for a concrete requirement or observed failure. Keep the smallest reasoning setting likely to succeed at that tier, where the host exposes it. Reuse known working routes and adjust task packets before escalating if specifications were insufficient.

For the current task, classify every known cheaper, authorized, plausibly capable route before the selected route:

- `FIT`: enough demonstrated/documented capacity, tools, context, and skills for this bounded contract.
- `TRIAL`: plausible but uncertain; eligible **only** for reversible, limited-scope tasks with objective checks and enough recovery budget. Prefer one useful trial over paying a larger worker by habit. This is not a dedicated identity or performance probe.
- `EXCLUDED(reason)`: missing a **specific** requirement (e.g., no required tool or context, prior comparable-task failure), task-specific risk, user restriction, or supported evidence that its expected **whole-task** cost would be higher. Avoid generic "not smart enough," "the larger model feels safer," or "better quality" assertions.

Select the first `FIT` or eligible `TRIAL` in the ranked list. A route can be skipped only with a specific documented reason; no cheaper `FIT`/`TRIAL` may be silently skipped. Keep the shortlist compact: include the selected route and **all plausibly cheaper** routes, not every expensive model in the catalog. Cache the available-model ladder between tasks, revisiting actual task-fit, verified routing, failures, and model availability when they change. When relative cost cannot be ranked confidently, label the ranking provisional and prefer a bounded trial of the **least costly plausibly capable** route under the available evidence rather than defaulting to a familiar larger model. For irreversible/high-risk work with insufficient confidence, do not gamble: exclude the unsuitable route with a concrete reason or block.

If a lower route fails, determine whether instructions, missing skills, environment, or model capability caused the problem. Correct the task packet and retry within the finite budget if economical; otherwise escalate **one capability/cost step at a time**, selecting the cheapest remaining qualified worker. Do not permanently blacklist a cheap model for one unrelated failure. An escalation is a new dispatch decision and repeats the cheapest-capable check; don't silently jump several tiers.


<a id="configure"></a>
## Select or configure automatically

1. **Explicit selection.** Pass supported model/effort controls or use a verified role mapping. Check precedence: a role can override defaults or per-call settings. A role named "budget" or a model named only in its prompt is insufficient.
2. **Session setup.** Create the smallest permitted temporary worker role/override when direct selection is unavailable. Keep the head unchanged and restrict worker tools/delegation where supported.
3. **Authorized local CLI.** A documented, already available CLI can create an explicitly configured worker when native tools cannot. Track its process/session, workspace, permission limits, outputs, effective route, and cancellation. Reuse its session for corrections only when supported. Never use it to evade a disabled feature, sandbox, account restriction, approval, or no-delegation policy. Verify this route independently; native-tool evidence does not verify CLI execution or vice versa.
4. **Persistent setup, only with authorization.** Modify project/user routing settings only with explicit user authorization or established project policy and host permission. File-write access alone is insufficient. Prefer project over global scope, preserve unrelated fields, validate syntax, and record changed values. If activation needs a reload/restart, mark it pending; do not terminate the head or pretend it is active.
5. **Block instead of silently upgrading or implementing.** With no eligible route, report the missing control/approval. Continue useful inspection/planning only. Do not spawn the head model by default or implement locally to avoid asking.

Prefer the least persistent valid mechanism; an available per-invocation CLI option need not wait for persistent setup. Do not enable new billing, providers, accounts, data destinations, or unrelated runtimes. Clean up only owned temporary resources/fields when their values still match your changes; do not overwrite later edits or remove roles another task uses. Leave authorized persistent changes intact unless agreed otherwise.

<a id="dispatch-gate"></a>
## Mandatory pre-dispatch decision

Maintain this compact head-side record in the ledger, not in every worker's prompt. `CANDIDATES` is a task-filtered shortlist of available authorized routes ordered from lowest to highest expected total usage. Include all plausibly cheaper routes and the selected model/effort, not the entire catalog; attach evidence through `EVIDENCE`. Each entry is `model-id@effort=FIT`, `=TRIAL`, or `=EXCLUDED(concrete reason)`, separated by semicolons. For `DISPATCH`, the selected `MODEL`/`EFFORT` must be the **first** `FIT` or `TRIAL` entry. For a blocked task use `NONE (reason)` if no candidate can be used. Host routing must still be real, not merely named in this text. Reuse unchanged evidence by reference. The same gate applies to read-only workers, resumes, corrections, and escalations. Preparing a packet does not authorize dispatch.

<!-- packet: dispatch-template -->
```text
TASK ID: <task being dispatched>
ROUND: <positive attempt number>
MODEL: <concrete supported model ID; never inherit/default/head>
EFFORT: <explicit supported setting, or UNSUPPORTED with limitation in EVIDENCE>
CANDIDATES: <ordered model@effort=FIT/TRIAL/EXCLUDED(reason) entries; include selected and all cheaper plausible routes>
CONTROL: <actual host arguments, verified role mapping, or authorized CLI selection>
ELIGIBILITY: <ECONOMICAL, EXCEPTION, or UNRESOLVED>
EVIDENCE: <route/capability/cost basis and uncertainty; cached record reference is enough>
APPROVAL: <NONE, or actual user authorization with applicable task/model scope>
LIMITS: <remaining attempts and finite work/output limits>
DECISION: <DISPATCH or BLOCK>
```

`ECONOMICAL` means the **first eligible cheapest-capable candidate** was selected after considering all plausibly cheaper options, not simply a model that costs less than the head and not a measured savings claim. `EXCEPTION` means a head-model/head-tier/higher-tier route or another user-restricted route: require actual prior approval covering this dispatch. `UNRESOLVED` means no eligible decision can be established and must produce `BLOCK`. Never record an approval the user did not give. Lower effort does not turn the head model into an eligible lower-tier worker. Exhausted attempt budgets block dispatch independently of model eligibility.

Before dispatch, briefly show task, **requested** model/effort, and why that route is the **cheapest capable** choice (or which cheaper candidates were excluded with task-specific reasons). Batch notices for parallel tasks. Do not ask for confirmation for every ordinary economical assignment. Ask only for a genuinely necessary approval or missing decision. User approval may authorize a worker exception without authorizing head implementation, and vice versa; keep those permissions separate.

<a id="evidence"></a>
## Observe execution without overclaiming

| State | Meaning |
| --- | --- |
| `CONFIRMED` | Authoritative host execution metadata or documented effective-routing output identifies the applied configuration. |
| `REQUESTED_ONLY` | Supported controls request a route, but execution has not been independently confirmed. |
| `UNKNOWN` | No trustworthy effective-route evidence, or an unresolved mismatch. |
| `UNAVAILABLE` | No permitted usable worker mechanism. |

Record the actual model/effort the evidence shows, not just a status label. Separately track metric, `relative_unit_cost = LOWER | SAME | HIGHER | UNKNOWN`, source, and uncertainty. Worker self-identification, names, and unloaded configuration are not runtime proof. A lower API rate cannot prove reduced subscription quota or total task cost.

For a supported but unconfirmed economical route, start with **one bounded useful task**, then inspect evidence before expanding. Do not spend calls on identity-only probes. If metadata remains unavailable, retain `REQUESTED_ONLY`: continue only bounded sequential work on that supported route, or obtain explicit approval for broader unverified use. Do not silently fan out or report savings as verified. A user's prohibition on any unverified routing overrides this allowance.

On a mismatch, stop new dispatches/resumes on that route. Cancel/join the active worker if safe and supported; protect partial writes and inspect useful output without discarding it blindly. Fix precedence/configuration or change to another permitted explicit route. An alternative mechanism needs its own evidence. Do not expand merely because a prompt says a cheaper model is running.

<a id="fallback"></a>
## Recovery without breaking the head/worker separation

| Situation | Required action |
| --- | --- |
| Economical route exists but no role is defined | Select it directly or configure it within permission; no manual setup chore for the user. |
| Host offers only a default spawn with unknown inheritance | Do not call it; investigate a permitted explicit route, otherwise block. |
| Known economical model, opaque quota weights | Use bounded routing with honest uncertainty, not invented savings. |
| Worker matches the head, even at lower effort | Obtain scope-specific approval first or choose a different eligible model. |
| Cheaper worker fails | Diagnose, refine, or escalate **one capable/price tier at a time** and record why earlier cheaper choices failed; no head takeover. |
| Mandatory skills/tools cannot reach a worker | Supply authorized complete guidance, change eligible route, or block implementation. |
| No eligible worker or configuration needs restart | Report the exact blocker; no silent premium-worker or direct-implementation fallback. |
| Head finds a one-line build error or integration conflict | Send a focused correction task to a worker. |
| Head resumes after context loss | Restore the orchestration boundary, route evidence, and approval scope before dispatch. |

The instruction skill cannot technically intercept a forbidden spawn. Use host-enforced model allowlists, ceilings, and tool restrictions when they exist and are authorized; never invent them or claim that this document installed them.
