---
name: frontend-twerkin
description: >-
  Runs functional/adversarial QA on local web or Expo apps, fixes
  failures, and retests workflows. Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: 0xdewy
  version: 2.0.0
  category: testing
  activation: explicit
  tags:
    - frontend
    - qa
    - functional
    - playwright
    - auto-fix
    - e2e
---

# Frontend Functional Tester

Use Playwright to verify frontend workflows, fix failures, and re-test. Scope the
pass to the user's request unless they explicitly ask for exhaustive QA.

Load `../common/patterns/quality.md`, `../common/patterns/execution-contract.md`,
and `../common/patterns/scaling.md`.
Run `scripts/detect_stack.sh` first. For web apps, load only the relevant
checklist from `references/adversarial-attacks.md` or
`references/css-audit-checklist.md`; when native is detected, load
`references/native-testing.md` and use existing Detox/native tooling (ask
before installing dependencies). Use Expo web only for browser-renderer checks,
not as evidence that native behavior passed.

## Modes

- `--quick`: smoke test critical path only. Budget: no agents.
- `--standard`: primary workflows across desktop/mobile, one fix loop.
- `--thorough`: exhaustive click-through and repeated fix loops to convergence.

## Workflow

1. Start or find the app server; record command, URL, and PID if started.
2. Build a route/workflow checklist from visible UI and project conventions.
3. Drive workflows with Playwright. Capture console errors, network failures,
   broken navigation, invalid states, and accessibility blockers.
4. Fix failures in scoped batches. Do not redesign unless required for function.
5. Re-run failing workflows; broaden only when the mode requires it.
6. Write `<WORKSPACE>/qa-report.md` with tested workflows, evidence, fixes,
   unresolved external dependencies, and screenshot paths. Keep generated test
   files in the workspace unless the user asks to retain them in the project.
7. Stop any server you started, unless the user asked to keep it running.

Final line:

```text
DONE: frontend-twerkin — <passed>/<total> workflows passing, fixes=<N>
```
