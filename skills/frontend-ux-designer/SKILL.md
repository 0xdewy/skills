---
name: frontend-ux-designer
description: >-
  Audits and fixes rendered UX with Playwright screenshots and computed
  CSS. Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: 0xdewy
  version: 1.0.0
  category: other
  activation: explicit
  tags:
    - frontend
    - ux
    - design
    - playwright
    - css
    - visual
    - layout
    - beauty
---

# Frontend UX Designer

Audit rendered UI with Playwright, fix targeted visual/UX issues, and verify the
screenshots. Do not run broad functional QA unless needed to inspect states.

Load `../common/patterns/quality.md`, `../common/patterns/execution-contract.md`,
and `../common/patterns/scaling.md`.
Use `scripts/audit.py <base-url> --output-dir <WORKSPACE>/ux-audit` for the
initial screenshot/computed-style inventory; pass `--routes` when scope is
explicitly limited.

## Modes

- `--quick`: one viewport/state, direct fixes. Budget: 0.
- `--standard`: key desktop/mobile states, one fix pass.
- `--thorough`: full responsive/state audit with repeated screenshot checks.

## Workflow

1. Start or identify the dev server. Use existing scripts/ports when possible.
2. Capture screenshots for chosen states and inspect computed CSS where useful.
3. Evaluate hierarchy, spacing, typography, color, alignment, responsiveness,
   overflow, and interaction affordances.
4. Apply scoped UI/CSS changes following the app's existing design system.
5. Write `<WORKSPACE>/ux-audit/design-critique.md` with prioritized findings
   tied to screenshot paths or computed CSS. In report-only mode, make no source
   edits.
6. Re-capture screenshots at desktop and mobile; verify no text overlap or
   broken layout.
7. Stop any server you started unless the user needs it running.

Final line:

```text
DONE: frontend-ux-designer — <N> UI fixes, screenshots verified=<yes|partial>
```
