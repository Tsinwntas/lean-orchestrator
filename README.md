<!-- lean-orchestrator-release: 1.7.0 -->
# Lean Orchestrator

**A model-agnostic Agent Skill for precise delegation, economical workers, and accountable head-agent review.**

Lean Orchestrator makes the main agent responsible for understanding your task, making design decisions, and giving workers clear implementation instructions. It discovers the host's capabilities and automatically selects or configures lower-cost capable workers where permitted. The head reviews their output, sends focused corrections, and integrates the result.

The objective is lower **total** usage, including head planning, worker context, retries, and verification. A small task may be better completed directly. No particular model, provider, or worker framework is required by the instructions.

## Install

Using the [Skills CLI](https://github.com/vercel-labs/skills) with its supported Node.js version (currently 22.20 or later):

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
automatically select or configure economical capable workers where permitted,
give them precise instructions and the relevant project skills, review and
correct their results, and deliver the integrated outcome.
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
| Routing | Uses supported per-call controls or temporary setup; persistent settings require authorization. |
| Worker instructions | Supplies bounded scope, procedures, relevant skills, finite limits, and verification. |
| Review | Checks actual artifacts rather than trusting a worker's completion claim. |
| Recovery | Handles corrections, stale results, timeouts, partial writes, and exhausted retry budgets. |
| Efficiency | Avoids unnecessary agents, duplicated context, repeated polling, and excessive head reviews. |
| Role separation | Workers use implementation skills without gaining authority to spawn further agents. |

## Compatibility and limits

This is an **instruction skill, not a model router or agent runtime**. A model can follow the planning protocol only to the extent its host exposes the required tools. The skill cannot create missing subagent APIs, force hidden model selection, override permissions, or guarantee lower quota use. It preserves the user-selected head model and falls back to direct execution when that is the sensible available path.

Requested routing is distinguished from confirmed execution. Model prices, token counts, and subscription quotas are different measurements. The skill does not present an assumed cheaper route as verified whole-task savings.

Workers need access to their required project instructions and implementation skills. Where supported, host permissions restrict delegation and other unnecessary tools; written prohibitions alone are not a security boundary. Installing the skill does not authorize new billing, new data destinations, or changes to global settings.

The [core instructions](skills/lean-orchestrator/SKILL.md) and bundled references are provider-independent and can be adapted to your own workflow. Actual behavior depends on the host and the model following the instructions.

## Offline checks

With Python 3.11 or later, from the repository root:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

These standard-library checks inspect metadata, portable links, packet contracts, release consistency, and malformed-input regressions. They make no LLM calls and do not prove live model behavior or cost savings.

## License

[MIT](LICENSE) — use, modify, and redistribute under its terms.
