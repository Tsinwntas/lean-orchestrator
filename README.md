<!-- lean-orchestrator-release: 1.9.0 -->
# Lean Orchestrator

**A model-agnostic Agent Skill: the head plans and reviews; economical workers do all implementation.**

Lean Orchestrator makes the main agent responsible for understanding your task, making design decisions, and giving workers clear implementation instructions. It discovers the host's capabilities and automatically compares available model/effort options and selects or configures **the cheapest capable worker** for each task where permitted. Before every dispatch, the head checks cheaper plausible alternatives before selecting an explicit worker model and reasoning setting using the host's supported controls. It reviews the output, sends focused corrections, and verifies the integrated result without doing implementation itself.

The objective is lower **total** usage, including head planning, worker context, retries, and verification. Small implementation tasks are batched or assigned to an existing eligible worker; the head does not take them over. No particular model, provider, or worker framework is required by the instructions.

## Install

Using the [Skills CLI](https://github.com/vercel-labs/skills) with the Node.js version required by that CLI:

```bash
npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator
```

For availability across projects:

```bash
npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator -g
```

For manual installation, copy the complete [`skills/lean-orchestrator/`](skills/lean-orchestrator/) directory into your host's supported skills location. Include its `references/` directory and `LICENSE`, not just `SKILL.md`. The repository's Python checks and GitHub workflow are not runtime requirements.

## Use

Activate the skill in your agent, or ask:

```text
Use Lean Orchestrator for this task. Make the design decisions yourself,
automatically rank eligible workers and select or configure the cheapest capable model/effort for each task,
delegate all implementation with precise instructions and relevant project
skills, review results, and send corrections back to workers. Do not implement
changes yourself or spawn workers that inherit your model by default.
```

```text
User task
  -> Head: settle requirements, inspect project skills, establish worker routing
  -> A0: exact assignment -> worker result -> head verification and acceptance
  -> A1: dependent assignment -> worker result -> head requests a correction
  -> A1, next round -> corrected result -> head verification and acceptance
  -> Head: integrated checks and delivery
```

Independent work can run in parallel when its resources and outputs do not conflict. Dependent work waits for accepted inputs that are actually available to its worker.

## What the skill controls

| Responsibility | Behavior |
| --- | --- |
| Planning | The head settles architecture, interfaces, edge cases, and acceptance criteria. |
| Routing | Finds all plausibly cheaper eligible workers, checks task fit, selects the cheapest capable model/effort, and verifies explicit selection before every spawn or retry. |
| Escalation | Tries bounded reversible work on a smaller plausible worker before moving up; records task-specific reasons for skipping cheaper models. |
| Worker instructions | Supplies bounded scope, procedures, relevant skills, finite limits, and verification. |
| Review | Checks actual artifacts rather than trusting a worker's completion claim. |
| Recovery | Handles corrections, stale results, timeouts, partial writes, and exhausted retry budgets. |
| Efficiency | Avoids unnecessary agents, duplicated context, repeated polling, and excessive head reviews. |
| Role separation | The head does not implement, including small fixes. Workers use implementation skills but cannot delegate further. |
| Premium workers | Head-model, head-equivalent-tier, and higher-tier workers need prior user approval for the specific scope. |

## Compatibility and limits

This is an **instruction skill, not a model router or agent runtime**. A model can follow the planning protocol only to the extent its host exposes the required tools. The skill cannot create missing subagent APIs, force hidden model selection, override permissions, or guarantee lower quota use. It preserves the user-selected head model. When no eligible worker route exists, the head reports the implementation blocker rather than silently using premium workers or doing implementation itself. Explicit user instructions may relax a boundary for a defined scope; ordinary task requests do not.

Requested routing is distinguished from confirmed execution. Model prices, token counts, and subscription quotas are different measurements. The skill does not present an assumed cheaper route as verified whole-task savings. A supported but unconfirmed route starts with one bounded useful assignment; routing mismatches stop further dispatches on that route.

Workers need access to their required project instructions and implementation skills. Where supported, host permissions restrict delegation and other unnecessary tools; written prohibitions alone are not a security boundary. Installing the skill does not authorize new billing, new data destinations, or changes to global settings.

The [core instructions](skills/lean-orchestrator/SKILL.md) and bundled references are provider-independent and can be adapted to your own workflow. Actual behavior depends on the host and the model following the instructions.

## Offline checks

With Python 3.11 or later, from the repository root:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

These standard-library checks inspect metadata, portable links, packet contracts, release consistency, dispatch records, and malformed-input regressions. They make no LLM calls and do not prove live model behavior or cost savings.

## License

[MIT](LICENSE) — use, modify, and redistribute under its terms.
