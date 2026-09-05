---
name: student-counsel
description: >-
  Executes substantive work, verifies hard requirements, then refines it
  against an evidence-backed beauty rubric for coherence, economy, proportion,
  legibility, honesty, and fit. Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 2.0.0
  category: quality
  activation: explicit
  tags:
    - beauty
    - quality
    - socratic
    - refinement
---

# Student Counsel

Produce correct work, then refine qualities that strict requirements often
leave unspecified. Beauty is a defeasible design prior, never proof.

Load `../common/patterns/quality.md` and
`../common/patterns/execution-contract.md`. Load `references/beauty-criteria.md` before
review and `references/socrates-prompt.md` only when dispatching a reviewer.

## Modes

- `--quick`: direct work plus self-check; zero reviewers.
- `--standard`: one independent Socratic review; cap 2 revisions.
- `--thorough`: Socratic review plus one domain/aesthetic reviewer; cap 3.

## Workflow

1. Write `FORM.md`: task, mode/cap, 2-5 hard acceptance criteria, verification,
   intended audience, and one north-star sentence.
2. Produce the complete work and verify hard criteria first.
3. If criteria fail, fix them before aesthetic review.
4. Review each beauty dimension with cited evidence. Reviewers return
   `BEAUTIFUL`, `NEEDS_REVISION`, or `UNCERTAIN` plus one highest-value change.
5. Revise only concrete defects, re-run hard verification, and stop at the cap.

`BEAUTIFUL` requires every hard criterion to pass and no material rubric defect.
Reviewer agreement is not evidence; the orchestrator owns the verdict. Report
`PARTIAL` when correctness or a material defect remains.

```text
DONE: <WORKSPACE> — BEAUTIFUL|PARTIAL after <N> revisions, verification=<result>
```
