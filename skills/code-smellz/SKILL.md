---
name: code-smellz
description: >-
  Finds and fixes repository-wide correctness, security, architecture, and
  maintainability problems with bounded review. Only use when explicitly
  requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 2.0.0
  category: meta
  activation: explicit
  tags:
    - refactoring
    - code-quality
    - bugs
    - optimization
    - multi-agent
---

# Code Smellz

Find and fix correctness, maintainability, architecture, and security problems
without changing intended behavior.

Load `../common/patterns/orchestration.md`, `../common/patterns/activation.md`, `../common/patterns/execution-contract.md`,
`../common/patterns/quarantine-loop.md`, `../common/patterns/workspace.md`,
and `../common/patterns/scaling.md`. Use `../common/scripts/detect_runner.py` and `measure_loc.py`.
At dispatch, use `references/subagent-prompts.md` to load the shared contract and
only the active role prompt.

## Activation

Second gate: confirm via `../common/ROUTING.md` that the task is
quality/correctness cleanup, not size-only reduction, pure review, or a
single obvious fix.

## Modes

- `--quick`: direct review/fix, or at most the 1-2 relevant agents. Budget: 0-2.
- `--standard`: dispatch the 2-3 roles justified by pre-pass evidence, once.
  Budget: 3.
- `--thorough`: all four roles, repeat shared loop to convergence, cap 5.

## Agents

Bug Hunter, Code Minimizer, Architecture Optimizer, Security Auditor. Each is
read-only and writes one findings JSON file.

## Workflow

Run `../common/patterns/quarantine-loop.md` under the selected mode. Use this
finding schema:
`{id, category, file, lines, severity, confidence, description, test_or_check,
estimated_risk, patch}`. Apply small batches in order: correctness, security,
architecture, minimization. Feed optional static/dependency checks to agents and
record unavailable checks rather than failing the run.

Final line:

```text
DONE: <WORKSPACE> — <N> fixes applied across <M> iterations, verification <passed|partial|blocked>
```
