---
name: skill-lab
description: >-
  Creates, refines, evaluates, and publishes SKILL.md behavior packs. Only
  use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 2.0.0
  category: meta
  tags:
    - skills
    - development
    - workflow
    - publishing
---

# Skill Lab

Create or improve a reusable skill: `SKILL.md` plus optional `references/`,
`scripts/`, `templates/`, `assets/`, and `evals/`.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`. For Codex-system
skills, also follow the local system `skill-creator` instructions if available.

## Workflow

1. Confirm the behavior deserves a skill: repeated workflow, specialized domain,
   reusable outputs, or tool integration.
2. Decide who invokes it. Model-invocable skills get concise TRIGGER/SKIP
   boundaries in the description; costly workflows and personas set
   `disable-model-invocation: true` and say they run only when explicitly
   requested. Then define inputs, workflow, safety, output, and verification.
3. Keep `SKILL.md` small. Put long prompts, examples, templates, and data in
   lazy-loaded files.
4. Add scripts/templates only when they reduce repeated work.
5. Add or update evals when triggers, output contracts, safety, or behavior
   change.
6. Validate YAML/frontmatter, referenced paths, and eval JSON.

Good skills are concise, decisive, and scoped. Avoid embedding full tutorials in
`SKILL.md`.

Final line:

```text
DONE: skill-lab — <skill-path> created/updated, evals=<yes|no>
```
