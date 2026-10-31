---
name: shrinkray
description: >-
  Cleans a repository while preserving behavior: removes dead code,
  duplication, and verbosity, or fixes correctness and security defects with
  --focus, verifying every change. Only use when explicitly requested.
disable-model-invocation: true
---

# Shrinkray

Clean a repository without changing intended behavior. Never commit.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`. Load `references/subagent-prompts.md` only
when dispatching a role.

## Focus

- `--focus size` (default): dead code, unreferenced files, duplication,
  verbosity.
- `--focus correctness`: real defects, plus localized structural fixes with a
  measurable gain.
- `--focus security`: reachable vulnerabilities and high or critical reachable
  dependency advisories (`npm audit`, `pip-audit`, `cargo audit`,
  `govulncheck` when installed).
- `--focus all`: all three.

Not this skill: build minification, a findings-only review (`red-team`), a
PR or diff review (`pr-smellz`), or one obvious fix (just make it).

Work directly by default. Dispatch the focus's roles only when the target is
too large for one context: `--standard` 1-3 roles chosen from the evidence,
`--thorough` adds the size structural roles. Cap 5 iterations.

## Loop

1. **Setup.** Resolve `WORKSPACE` and read the project goal from its README
   or manifest. Run `git status --short`; outside git,
   warn and snapshot files before editing. Detect the runner with
   `scripts/detect_runner.py`, measure LOC with `scripts/measure_loc.py`, and
   run the tests once as the baseline. Record all of it in `session.json`.
2. **Evidence.** Run `scripts/less_code_pass.py <repo> <WORKSPACE>`
   (add `--test-command` when the runner is certain). `lc` applies and
   verifies its own changes; record `total_loc_removed`, or the skip reason
   when `ran` is false. Then run `scripts/deadcode_scan.py` and
   `scripts/dependency_index.py` with the same arguments. A missing tool is
   recorded, not fatal. Every focus uses these as leads.
3. **Find.** Review directly or dispatch roles. Findings are JSON:
   `{id, category, file, lines, description, evidence, confidence, source_tool}`.
   Rank tool-certified findings above model-only ones.
4. **Triage.** Drop low confidence. Where findings overlap, keep the larger
   gain. Flag public-API changes for human review instead of applying. Write
   `STAGED_CHANGES.md` before any edit. Nothing left: go to the report.
5. **Apply.** Order: correctness, security, unreferenced files, dead code,
   consolidation, verbosity. For each change, edit, save that change's diff
   to `WORKSPACE/changes/<id>.patch`, run the cheapest check (type checker,
   `py_compile`, `node --check`), and reverse the patch if it adds errors.
6. **Verify.** Run the full suite and available type-check and lint gates.
   On failure, reverse this iteration's patches newest first until green. If
   a reverse fails, stop and report the touched files and failed command.
7. **Repeat** from step 2 until a rescan finds no high or medium findings,
   fewer than 2 changes survive an iteration, or 5 iterations ran. Flag the
   run unstable when most of an iteration's changes were reverted.

## Report

LOC and test results before and after, changes kept and reverted per
category, and items left for human review. Tell the user to review
`git diff` and commit themselves. End with:

```text
DONE: <WORKSPACE> — <kept> changes across <iterations> iterations, -<lines> LOC (-<pct>%), verification <passed|partial|blocked>
```
