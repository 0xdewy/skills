---
name: red-team
description: >-
  Read-only adversarial review through user, security, and
  architecture/economics perspectives, merged into one prioritized report.
  Only use when explicitly requested.
disable-model-invocation: true
---

# Red Team

Adversarially review one deliverable and produce a prioritized findings report.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`. Load `references/persona-prompts.md` only
when spawning.

## Activation

Find issues in an existing deliverable. Building or fixing is `goal` or
`project-manager`; a diff-scoped review is `pr-smellz`. This skill writes
reports only; it never edits the target.

## Modes

- `--quick`: orchestrator reviews directly through the highest-risk lens. Budget:
  0 agents.
- `--standard`: spawn User, Hacker, and Red-teamer once in parallel. Budget: 3.
- `--thorough`: standard plus one targeted follow-up wave if needed.

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
5. Write `REPORT.md`: a short summary with counts, then prioritized findings,
   then recommended next actions. On each finding, note which personas raised
   it (a cross-persona signal) and any conflict between them.

Finding schema: `{id, persona, severity, confidence, title, evidence, impact,
recommendation}`.

Final line:

```text
DONE: <WORKSPACE> — <N> findings (<critical>/<high>)
```
