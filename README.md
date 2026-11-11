# Lean Orchestrator

**A model-agnostic Agent Skill for cost-aware task delegation and sub-agent coordination.**

Lean Orchestrator turns a capable agent into the **head agent** for a multi-step task. The head designs the solution, divides the work into precise assignments, chooses suitable execution tools or workers, reviews their results, sends corrections when necessary, and integrates the verified outcome.

The objective is to use as little total LLM quota as practical **without compromising correctness**. Delegation is optional: when spawning a worker would cost more than doing the work directly, the head should not delegate.

## Installation

Install with the [Skills CLI](https://github.com/vercel-labs/skills) (requires Node.js 22.20+):

```bash
npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator
```

The installer lets you select a supported agent. To make the skill available across projects, add `-g`:

```bash
npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator -g
```

For manual installation, copy the complete [`skills/lean-orchestrator/`](skills/lean-orchestrator/) directory, including `references/`, into your agent's supported skills directory. Agents without a skill installer can also read the skill instructions directly, subject to their available tools.

## Usage

Activate `lean-orchestrator` through your agent's skills interface, or ask:

```text
Use the lean-orchestrator skill for this task. Make the important
planning decisions yourself, give workers precise assignments,
use the cheapest capable execution path, review every result,
and correct or integrate the work before finishing.
```

## How it works

```text
User request
    |
    v
Head agent: inspect project skills, design solution, split tasks
    |
    +--> A0: explicit instructions --> Worker 0 --> result
    |                                        |
    +<--------------- Head reviews and accepts A0
    |
    +--> A1: dependent assignment --> Worker 1 --> result
    |                                        |
    +<--------------- Head requests a focused correction
    |
    +--> A1, round 2 -----------> Worker 1 --> corrected result
    |                                        |
    +<--------------- Head verifies and accepts A1
    |
    v
Head validates integrated result and reports to user
```

Independent tasks may run in parallel. Dependent tasks start **only after the head accepts their prerequisites**.

### Key behaviors

- **Head-first reasoning:** the head resolves requirements, interfaces, dependencies, and acceptance checks.
- **Cost-aware routing:** prefer deterministic tools, otherwise use the lowest-cost capable available worker; account for delegation overhead and retries.
- **Precise task packets:** workers receive fixed inputs, allowed edits, applicable project skills, exact procedures, and verification criteria.
- **Closed-loop review:** the head accepts, corrects, replans, or blocks worker results and stays accountable for the final outcome.
- **Project-skill continuity:** workers receive the project guidance and implementation skills relevant to their assignments.
- **No recursive delegation:** workers remain workers even if the orchestration skill is visible to them. Host-level permission restrictions should be used when available.
- **Graceful fallback:** if workers, cheaper models, or resumable sessions are unavailable, the head uses the capabilities it has.

## Requirements and limitations

Lean Orchestrator provides **instructions, not an agent runtime**. It cannot independently create workers, select unavailable models, grant tool permissions, or guarantee reduced cost. Actual delegation and model routing depend on the executing environment. It does not claim benchmarked quota savings.

The portable skill is in [`skills/lean-orchestrator/SKILL.md`](skills/lean-orchestrator/SKILL.md); its supporting references are installed alongside it. The repository's `.github/`, `scripts/`, and `tests/` directories are only for offline quality checks and are **not needed** in the installed skill.

## Validation

The repository includes dependency-free Python structural checks:

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

They verify metadata and the documented task contract, not live agent behavior or token savings.

## License

[MIT](LICENSE) — use, modify, and redistribute the skill under the license terms.
