---
name: code-smellz
description: >-
  Finds and fixes repository-wide correctness, security, architecture, and
  maintainability problems with bounded review. Only use when explicitly
  requested.
disable-model-invocation: true
---

# Code Smellz

Find and fix correctness, maintainability, architecture, and security problems
without changing intended behavior.

Load `../common/patterns/execution-contract.md`,
`../common/patterns/quarantine-loop.md`, and `../common/patterns/scaling.md`. Use `../common/scripts/detect_runner.py` and `measure_loc.py`.
Load `references/subagent-prompts.md` only at dispatch.

## Activation

Quality and correctness cleanup only. Size-only reduction is `shrinkray`; a
report without fixes is `red-team`; a single obvious fix needs no skill.

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
