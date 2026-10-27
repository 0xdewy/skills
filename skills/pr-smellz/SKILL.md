---
name: pr-smellz
description: >-
  Reviews PR diffs for introduced risks, anchoring findings to changed
  lines; read-only unless --fix is explicit. Only use when explicitly
  requested.
disable-model-invocation: true
---

# PR Smellz

Review behavior and complexity introduced by a pull request or branch diff. Findings lead;
every finding must be actionable, independently verified, and anchored to a
changed line, including a removed line or deleted file. Default is read-only.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`. Run
`scripts/changed_scope.py` for locally available refs. When dispatching, load
`references/reviewer-prompts.md` and only the selected lenses.

## Activation

The target is a PR or branch diff. Use
`code-smellz` for whole-repo cleanup and `red-team` for a broad read-only review
of a non-PR deliverable. Address already-supplied review comments directly.

## Inputs

- PR URL/number or local `HEAD`.
- Base ref/SHA when it cannot be inferred; never guess an ambiguous base.
- Optional `--fix`; without it, do not edit.

## Modes

Unflagged default is `--standard`. Pareto and Correctness always run. Product,
Maintainability, and Security run when the trigger matches or relevance is
uncertain. Skip one only when the diff cannot meet its trigger.

- Product: a user, API caller, or operator can observe the change, including
  UI, CLI, public API, migration, rollback, or operational behavior.
- Maintainability: new or changed structure, wrappers, duplication, branching,
  or indirection.
- Security: trust boundary, removed safeguard, dependency, configuration, or
  newly reachable input.
- `--quick`: Pareto, Correctness, and every triggered Product, Maintainability,
  or Security check, inline. Spawned passes: 0. `independent: no`.
- `--standard`: those two plus every triggered conditional lens. One wave.
- `--thorough`: all 5 lenses, including weak triggers. One wave. A lens past
  available concurrency runs inline.

Pareto is highest priority. Consider subtraction before additive fixes.
Priority does not override severity or justify removing required behavior or
security safeguards.

## Workflow

1. State `mode: <tier> (<reason>); passes: <lenses>; independent: yes|no`.
   `independent: no` means the passes shared a context. For a PR number/URL,
   use `gh pr view --json
   title,body,baseRefName,baseRefOid,headRefName,headRefOid,files`; otherwise
   use local git and the provided base.
2. When base/head objects exist locally, run `scripts/changed_scope.py --base
   <ref> --head <ref>`. Otherwise use `gh pr diff <pr> --patch`. Fetch missing
   objects only with permission. Never check out a PR over a dirty worktree.
   Record base, head, merge-base, paths, both-side hunks, additions, and
   deletions. If no diff exists, stop.
3. Read repository guidance and only the callers, contracts, schemas, and tests
   needed. Write `<WORKSPACE>/evidence-pack.md` once: documented goal,
   requirements, and motivation, separate from parent assumptions; the three
   SHAs; the scope summary; every hunk of the full diff; numbered excerpts
   `E<n> <sha> <path>:<start>-<end>`. Size excerpts by the callers, contracts,
   schemas, and tests the change needs, not by the diff. The pack is neutral
   and omits lens findings. Do not drop a hunk.
4. Give each lens the pack path and its prompt. It may read only that pack. It
   returns the JSON object and does not write files or search the repo. The
   parent writes `findings-<lens>.json`. Spawned lenses get a fresh context.
   Inline passes use the same prompts and set `independent: no`.
5. For an evidence request, append the SHA-pinned excerpt and rerun only that
   lens once. Requests that remain are coverage gaps.
6. Validate every finding: the diff introduced or worsened it; `path`, `line`,
   and `side` name an added, modified, or removed line; evidence supports
   impact; and a trace or focused check can reproduce it. An unavailable check
   does not make a high-impact concern false. Drop style and speculative findings.
7. Run targeted tests or static checks when available. Record skips and residual risk.
8. Deduplicate and write `<WORKSPACE>/PR_REVIEW.md`. Findings first, by severity,
   Pareto first within a severity, then coverage gaps, questions, verification,
   and a short summary.
9. Only with `--fix`, apply minimal accepted fixes and re-run targeted checks.
   Never commit or post review comments unless separately requested.

Finding schema:
`{id, lens, severity, confidence, title, path, line, side, introduced_by_diff,
evidence, impact, verification, recommendation}`.
`side` is `old` for a removed line and `new` for an added or modified line.

If there are no findings, say so and list coverage gaps and test gaps.
Do not inflate the report with pre-existing issues.

Final line:

```text
DONE: <WORKSPACE>/PR_REVIEW.md — <N> findings (<critical>/<high>), checks=<passed|partial>
```
