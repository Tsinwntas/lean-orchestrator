# Lean Orchestrator

**A provider-independent Agent Skill that plans complex tasks, configures economical workers when permitted, and coordinates their results.**

Lean Orchestrator turns an agent into a **head agent**: it makes the architectural decisions, decomposes the request into precise assignments, selects or configures suitable lower-cost workers, passes along relevant project skills, verifies results, and corrects failures before integrating the completed work.

Its goal is to **minimize total expected model usage without compromising correctness**. If direct execution is cheaper or worker routing is unavailable, the head avoids unnecessary delegation.

## Install

With the [Skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator
```

To make it available across projects:

```bash
npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator -g
```

Alternatively, copy the entire [`skills/lean-orchestrator/`](skills/lean-orchestrator/) directory, including `references/`, into your agent's supported skills directory. Any agent that can read skill instructions can use the planning protocol; execution features depend on the tools that agent actually has.

## Use

Activate `lean-orchestrator` through your agent's skill interface, or say:

```text
Use Lean Orchestrator for this task. Plan the work yourself, automatically
select or configure the lowest-cost capable workers if permitted, give
workers exact instructions and relevant project skills, review their work,
and deliver the verified result.
```

## How it works

```text
User request
     |
     v
HEAD: understand request + discover project skills
     |
     v
HEAD: discover available models and worker-routing controls
     |-- select cheaper worker per call, if supported
     |-- otherwise configure a temporary worker route, if supported
     |-- otherwise use permitted existing tools / direct execution
     v
HEAD: design solution and define A0, A1, ...
     |
     +--> A0: exact task packet --> WORKER --> evidence
     |                                 |
     +<--------- HEAD verifies and ACCEPTS A0
     |
     +--> A1: dependent task ---> WORKER --> evidence
     |                                 |
     +<--------- HEAD detects issue and requests correction
     |
     +--> A1 round 2 ---------> WORKER --> fixed evidence
     |                                 |
     +<--------- HEAD verifies and ACCEPTS A1
     |
     v
HEAD: run integration checks and deliver result
```

Independent, nonconflicting tasks may run in parallel. Dependent work waits for head acceptance.

## What it does

- **Automatic worker routing:** discovers host-supported models and agent tools, chooses economical routes, and configures temporary workers when permitted—without requiring a preconfigured cheap worker.
- **Head-first reasoning:** centralizes architecture, requirements, interfaces, dependencies, and test design to avoid making cheap workers guess.
- **Precise task packets:** gives workers exact scope, steps, required project guidance, implementation skills, acceptance checks, and stop conditions.
- **Closed-loop orchestration:** receives reports, reviews artifacts, issues targeted corrections, and escalates only when necessary.
- **Project-skill continuity:** ensures workers can use applicable project instructions and skills even when worker contexts are isolated.
- **No recursive delegation:** worker packets prohibit spawning further agents; host-enforced restrictions are used when available.
- **Whole-run efficiency:** considers head reasoning, worker setup, context, reviews, and retries; uses deterministic tools or direct execution when cheaper.
- **Graceful fallback:** continues productively when models cannot be switched, workers cannot be spawned, or capabilities cannot be verified.

## Requirements and limitations

Lean Orchestrator is a **skill, not a separate model router or agent runtime**. Actual worker spawning, model selection, temporary configuration, skill access, and messaging depend on what the running environment exposes. The skill never bypasses host permissions or silently changes persistent user settings. When a cheaper worker route cannot be verified, it must not claim verified quota savings.

The installable entry point is [`skills/lean-orchestrator/SKILL.md`](skills/lean-orchestrator/SKILL.md). Its reference files install alongside it; repository CI and test files are not required at runtime.

Cost savings and compatibility across agent hosts have **not yet been formally benchmarked**.

## Offline validation

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

These dependency-free checks validate metadata and required instruction contracts. They do **not** simulate live sub-agent calls or measure model costs.

## License

[MIT](LICENSE) — free to use, modify, and redistribute under the license terms.
