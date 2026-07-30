# Quality Patterns

Loaded by skills in the Quality category and any skill that iteratively
refines output through adversarial review: student-counsel, look-for-flaws,
implementer, frontend-twerkin, frontend-ux-designer.

Read this at activation. Also load
`skills/common/patterns/execution-contract.md` for artifact validation,
worktree safety, and final verification rules. Append discovered patterns at
completion.

## Contribution Format

```
### <Pattern Name>
- **Discovered by:** <skill>, <date>
- **Tags:** <tag1>, <tag2>
- **Pattern:** <one sentence>
- **Why:** <one sentence>
```

---

### Convergence Cap
- **Discovered by:** student-counsel, brainstormers, 2026-05-11
- **Tags:** iteration, convergence, cap
- **Pattern:** Set an explicit maximum iteration count (5-8 rounds) with a
  meaningful name for the cap. When reached, acknowledge it explicitly.
- **Why:** Without a cap, iterative skills loop forever on problems with no
  perfect solution. A named, meaningful cap transforms failure-to-converge
  from an error into an acknowledged limitation of the method.

### Acceptance Criteria First
- **Discovered by:** skills review, 2026-06-17
- **Tags:** quality, acceptance, verification
- **Pattern:** Before producing or reviewing work, write 2-5 observable
  acceptance criteria tied to the user's request.
- **Why:** Reviewers cannot reliably judge "good" unless they know what must be
  true in the final artifact. Criteria turn taste into a checkable floor.

### No Pass With Failed Criteria
- **Discovered by:** student-counsel hardening, 2026-06-17
- **Tags:** quality, gate, review
- **Pattern:** A reviewer may request polish beyond the criteria, but it may not
  declare success while any observable acceptance criterion fails.
- **Why:** Aesthetically persuasive work that fails the user's actual task is
  still wrong.

### Scored Rubric With Evidence
- **Discovered by:** frontend-ux-designer, implementer, 2026-06-17
- **Tags:** scoring, evidence, review
- **Pattern:** Score each review dimension separately and cite the evidence:
  file/line, screenshot, command output, artifact path, or exact output text.
- **Why:** A single overall score hides the failure mode. Evidence-backed
  sub-scores let the fixer act without guessing.

### Independent Final Verification
- **Discovered by:** one-shot-project hardening, 2026-06-17
- **Tags:** verification, orchestrator, completion
- **Pattern:** The top-level orchestrator verifies the final artifact against
  acceptance criteria even when a reviewer, PM, or dialectic says it is done.
- **Why:** Subagents are advisors. Final responsibility belongs to the agent
  delivering the result to the user.

### Partial Is A Valid Outcome
- **Discovered by:** implementer, code-smellz, 2026-06-17
- **Tags:** completion, blockers, honesty
- **Pattern:** When the loop cap is reached or essential verification is blocked,
  emit a `PARTIAL` result with what works, what was checked, and what remains.
- **Why:** Pretending convergence happened is worse than shipping a useful
  partial artifact with honest blockers.
