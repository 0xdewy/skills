---
name: red-team
description: >-
  Read-only adversarial review through user, security, and
  architecture/economics perspectives, merged into one prioritized report.
  Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: user
  version: 1.0.0
  category: meta
  activation: explicit
  tags:
    - adversarial
    - review
    - coworker
    - multi-agent
    - security
    - ux
    - red-team
---

# Red Team

Adversarially review one deliverable and produce a prioritized findings report.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`. Load persona prompts only when spawning.

## Activation

Second gate: confirm via `../common/ROUTING.md` that the job is to *find*
issues in an existing deliverable, not build/fix work or a specialized
domain/security audit. This skill writes reports only; it never edits the target.

## Modes

- `--quick`: orchestrator reviews directly through the highest-risk lens. Budget:
  0 agents.
- `--standard`: spawn User, Hacker, and Red-teamer once in parallel. Budget: 3.
- `--thorough`: standard plus one targeted follow-up wave if needed.

Do not use this for implementation. It writes reports only.

## Personas

- User: requirement gaps, confusing flows, missing states, trust failures.
- Hacker: exploitable bugs, unsafe inputs, auth/data risks, dependency issues.
- Red-teamer: architecture, economics, scale, coupling, failure modes.

## Workflow

1. State the mode line from `../common/patterns/scaling.md` (`mode: <tier> (<reason>); budget: <max
   personas>`), then write `TARGET.md` with target path/spec, acceptance
   criteria, and scope.
2. At `--quick`, write `findings-direct.json`; otherwise dispatch personas with
   owned files: `findings-user.json`, `findings-hacker.json`,
   `findings-redteam.json`.
3. Validate JSON exists and parses. Re-run only missing/invalid roles.
4. Merge duplicates, preserve disagreements, sort by severity then confidence.
5. Write `REPORT.md` with summary, cross-persona signals, conflicts, prioritized
   findings, and recommended next actions.

Finding schema: `{id, persona, severity, confidence, title, evidence, impact,
recommendation}`.

Final line:

```text
DONE: <WORKSPACE> — <N> findings (<critical>/<high>)
```
