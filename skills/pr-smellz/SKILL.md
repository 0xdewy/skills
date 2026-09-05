---
name: pr-smellz
description: >-
  Reviews PR diffs for introduced risks, anchoring findings to changed
  lines; read-only unless --fix is explicit. Only use when explicitly
  requested.
license: MIT
disable-model-invocation: true
metadata:
  author: user
  version: 1.0.0
  category: quality
  tags:
    - pull-request
    - code-review
    - correctness
    - security
    - regression
    - testing
---

# PR Smellz

Review only behavior introduced by a pull request or branch diff. Findings lead;
every finding must be actionable, independently verified, and anchored to a
changed line. Default is read-only.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`. Run
`scripts/changed_scope.py` for locally available refs. When dispatching, load
`references/reviewer-prompts.md` and only the selected lenses.

## Activation

Confirm via `../common/ROUTING.md` that the target is a PR/diff. Use
`code-smellz` for whole-repo cleanup and `red-team` for a broad read-only review
of a non-PR deliverable. Address already-supplied review comments directly.

## Inputs

- PR URL/number or local `HEAD`.
- Base ref/SHA when it cannot be inferred; never guess an ambiguous base.
- Optional `--fix`; without it, do not edit.

## Modes

- `--quick`: small, low-risk diff; review directly. Budget: 0 agents.
- `--standard`: select 2 relevant lenses for a multi-area or moderate-risk diff.
  Budget: 2 agents, one wave.
- `--thorough`: all 3 lenses for large/high-risk changes such as auth, payments,
  migrations, concurrency, cryptography, or public APIs. Budget: 3 agents.

## Workflow

1. State the mode line. For a PR number/URL, use `gh pr view --json
   title,body,baseRefName,baseRefOid,headRefName,headRefOid,files`; otherwise use
   local git and the provided base.
2. When base/head objects exist locally, run `scripts/changed_scope.py --base
   <ref> --head <ref>`. Otherwise use `gh pr diff <pr> --patch` as the read-only
   scope; fetch missing objects only with permission when deeper context is
   required. Never check out a PR over a dirty worktree. Record the base/head,
   paths, hunks, additions, and deletions. If no diff exists, stop clearly.
3. Read repository guidance, the diff, changed files, and only the callers,
   contracts, schemas, and tests needed to understand changed behavior.
4. Review directly or dispatch selected lenses from
   `references/reviewer-prompts.md`. Reviewers are read-only and own separate
   JSON files.
5. Validate every finding: the PR introduced or worsened it; its location is an
   added/modified line; evidence supports impact; and a focused check or trace
   can reproduce the concern. Drop style preferences and speculative findings.
6. Run targeted tests/static checks for affected areas when available. Record
   unavailable checks and residual risk.
7. Deduplicate and write `<WORKSPACE>/PR_REVIEW.md`. Lead with findings ordered
   by severity, then questions/assumptions, verification, and a short summary.
8. Only with `--fix`, apply minimal accepted fixes and re-run targeted checks.
   Never commit or post review comments unless separately requested.

Finding schema:
`{id, lens, severity, confidence, title, path, line, introduced_by_diff,
evidence, impact, verification, recommendation}`.

If there are no findings, say so explicitly and list remaining test gaps or
unreviewed risk. Do not inflate the report with pre-existing issues.

Final line:

```text
DONE: <WORKSPACE>/PR_REVIEW.md — <N> findings (<critical>/<high>), checks=<passed|partial>
```
