---
name: pareto
description: >-
  Applies subtraction-first restraint to coding tasks: question necessity,
  prefer deletion and reuse, impose hard change budgets, and make every line
  justify its maintenance cost without weakening behavior, safety, or clarity.
  Only use when explicitly requested.
disable-model-invocation: true
metadata:
  activation: explicit
---

# Pareto

Minimize maintenance burden, not LOC. Preserve behavior, correctness, security,
clarity, and verification.

Before editing:

- Can no change solve it?
- Can deletion, simplification, configuration, or reuse solve it?
- What breaks if this action is skipped? If nothing, skip it.
- Is the complexity essential or accidental?

Set a hard, task-shaped budget for files, net-new code, dependencies, agents,
and iterations. Start at zero; raise it only with evidence.

Make the smallest local, reversible change. Add only what serves current
behavior or demonstrated risk. Verify narrowly, then stop. Treat no change as
success.

Compose with domain skills; their safety and correctness rules win. If this
skill adds ceremony, drop the ceremony.
