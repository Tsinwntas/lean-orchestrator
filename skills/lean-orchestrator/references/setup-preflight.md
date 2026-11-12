<!-- lean-orchestrator-release: 1.7.0 -->
# Routing setup

Read once before substantial delegation, then revisit only if capabilities change or a routing problem appears. This procedure is generic; the running host's tool contracts supply the concrete commands and model IDs.

<a id="discover"></a>
## Discover without expensive probing

Use advertised tools, authorized local configuration, help/schema, and existing worker definitions. Inspect only relevant configuration; do not dump credentials or scan an entire account. If local information is insufficient, consult official host documentation when accessible, matching the installed version rather than assuming the newest syntax applies.

Establish:

- Worker creation, model/effort selection, role permissions, cancellation, wait/resume, concurrency, and result retrieval capabilities.
- Eligible model choices and required tool, context, modality, and skill capabilities. Include only routes authorized for this project's data and budget.
- Effective head/worker models when exposed; inheritance and precedence of per-call, role, session, and persistent settings. A role may override a default or add a costly prompt.
- Whether contexts/files are shared or isolated; how artifacts, project instructions, and skills reach workers.
- Available cost evidence for the user's actual metric. Distinguish cached-input/output charges, tool costs, quota weights, and opaque subscription accounting. Use only information available, not guessed prices.

One bounded inspection pass should normally suffice. Investigate further only for a concrete unresolved blocker; prefer useful work over repeated configuration experiments. Cache findings with environment, relevant configuration, permission scope, and model availability. Availability in a general catalog does not prove account access.

<a id="configure"></a>
## Select or configure, in order

1. **Per-dispatch selection.** Reuse a suitable existing role or pass an allowed model/effort explicitly. Confirm how role settings interact with overrides. A role called "cheap" does not establish model identity or cost.
2. **Session-scoped setup.** Create the smallest permitted temporary role/override when per-call routing is unavailable. Keep the head model unchanged. Apply least-privilege worker tools and no worker delegation where supported.
3. **Persistent setup, only with authorization.** Project or user settings require explicit user authorization or established project policy covering that change, plus host permission. File-write access alone is not authorization. Invocation of this skill is not blanket approval to modify account/global defaults. Prefer project scope to global scope, preserve unrelated fields, validate syntax, and record just the values changed. If reload/restart is required, mark the change pending; do not terminate the head session or claim the route is active. Ask for necessary approval rather than repeatedly trying blocked changes.
4. **Fallback.** Use the best authorized route or execute directly. Explain a material limitation once, without making the user repeatedly reconfigure a host that offers no controls.

Do not enroll a new provider/account, transmit project data to an unapproved destination, enable paid overages, install a new runtime, or bypass a sandbox to obtain a cheaper model. A documented local command can be a valid routing mechanism only if already available and authorized; shell access does not create permission to evade a restriction.

Track temporary changes/resources you create. Revert only your own changed fields if their current values still match your changes. Do not overwrite later user edits or remove roles that other work is using. Leave explicitly authorized persistent changes intact unless their agreed lifetime was temporary.

<a id="evidence"></a>
## Separate routing evidence from cost evidence

| Routing state | Meaning |
| --- | --- |
| `CONFIRMED` | Authoritative host execution metadata or documented effective-routing output identifies the route actually applied. |
| `REQUESTED_ONLY` | A supported request/configuration selects a route, but actual execution has not been confirmed. Submitted arguments alone belong here. |
| `UNKNOWN` | Effective routing cannot be established, or observed execution contradicts the requested route without a resolved explanation. |
| `UNAVAILABLE` | No permitted usable delegation mechanism exists. |

Independently record `metric`, `relative_unit_cost = LOWER | SAME | HIGHER | UNKNOWN`, the evidence source, and any uncertainty. These labels are head bookkeeping, not literal API parameters. A worker's self-identification, role name, or a config file not yet loaded is not runtime proof. Never promote `REQUESTED_ONLY` merely because the worker says the chosen model ran.

A `LOWER` API price says nothing certain about a subscription's quota weights. Even a confirmed lower unit cost does not establish a lower total task cost: head context, worker context, tool charges, failures, and integration still matter.

For an unconfirmed but supported route, make a bounded first assignment do useful work; inspect returned host metadata before scaling up. When confirmation is impossible, keep the uncertainty explicit and decide using the available evidence. Do not ban all delegation because a host hides pricing; do not describe it as verified savings either.

<a id="fallback"></a>
## Decide without overclaiming

| Situation | Action |
| --- | --- |
| Economical capable route is usable | Select it automatically; dispatch only if whole-task economics justify it. |
| Route requested but execution opaque | Small useful assignment with a finite budget; do not assume savings or fan out broadly. |
| Requested cheap route resolves to the head/other model | Record the effective evidence, stop expanding that route, and diagnose precedence once or use a fallback. |
| Same-model worker has much smaller relevant context | Consider the actual estimated total, including review; smaller context can justify delegation without a different model. |
| Only known higher-cost workers are available | Use only for a necessary capability/quality or explicit latency benefit; otherwise direct/D0. |
| Required project skills or tools cannot reach worker | Transfer authorized requirements safely, choose a capable route, or retain the task at the head. |
| Configuration blocked or requires restart | Do not claim it succeeded; continue with current capabilities or request only a necessary approval. |
| No eligible worker | Complete useful work directly and state material limits. |

A concise routing disclosure is enough when relevant: "Worker model selected through the host; actual subscription quota impact is not exposed." Never report a precise quota percentage from an API-price proxy.
