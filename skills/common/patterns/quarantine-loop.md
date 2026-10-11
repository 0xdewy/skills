# Quarantine Loop Pattern

Converge-and-revert loop shared by `code-smellz` and `shrinkray`. They differ
only in agent roster, finding schema, apply order, and the gates they enable.
Load this alongside `execution-contract.md` (workspace, patch-only rollback,
`DONE:` line).

## The loop

- **Phase 0 — Setup & baseline.** Resolve `WORKSPACE` (see `execution-contract.md`).
  If a prior run's output dir exists, archive it (`mv … .prev`) before recreating.
  Read the one-sentence project goal from `CLAUDE.md` / `README.md` /
  `package.json` / `pyproject.toml`. Detect the test runner and baseline LOC with
  the shared scripts (`skills/common/scripts/detect_runner.py`,
  `measure_loc.py`). Run the baseline test suite once and record the pass rate.
  Run `git status`; if the project is not a git repo, warn that changes cannot be
  reverted with `git apply -R` and confirm before proceeding. Load the skill's
  ignore file (`.stinkyignore` / `.shrinkignore`, `.gitignore` syntax) into
  `exclusions.txt`. Write a `session.json` capturing iteration count, baseline
  LOC/tests, detected tool commands, and (for skills that support it) per-category
  quarantine state.
- **Phase 1 — Parallel dispatch.** Spawn the skill's read-only agents
  **simultaneously** (one message, one Task call each). Each gets the file list
  minus exclusions and the pre-computed analysis data the skill produces. Each
  writes one JSON findings file containing **unified-diff patches** — never prose
  fixes the orchestrator must re-interpret. Agents READ and REPORT only; no file
  changes in this phase. Wait for all agents before proceeding.
- **Phase 2 — Triage.** Merge findings, sort by severity/confidence then LOC
  saved. Detect line conflicts (two findings touching the same lines → keep the
  larger save, skip the other). Apply safety filters (skill-specific: e.g. skip
  low-confidence sub-10-LOC saves, flag public-API surfaces for human review).
  Check quarantine state and skip any category already quarantined. Write
  `STAGED_CHANGES.md` listing every planned change **before** applying anything,
  so the user can inspect and abort. If no HIGH/MEDIUM findings remain, skip to
  the report.
- **Phase 3 — Apply.** Save a working-tree checkpoint
  (`git diff > pre-iter-N.diff`). Apply in the order the skill's `SKILL.md`
  gives. For each finding: if it has a `patch`, `git apply --check` then `git apply`;
  if `--check` fails (file changed since the agent read it), fall back to a manual
  edit from the description. **After each individual change**, run the cheapest
  available correctness check (type checker, or `py_compile` for Python) and
  `git apply -R` that single patch immediately if it introduces new errors. Log
  every applied change to `session.json → history` with its patch path so revert
  is O(1).
- **Phase 3.3 — Second minimizer pass.** After a patch lands and passes its
  check, re-read the result and ask whether it can shrink further: a new
  helper may itself be inlinable, and removing dead code can make adjacent
  code dead. New candidates go back into Phase 2 within the same iteration,
  bounded by the iteration cap.
- **Phase 4 — Verify.** Run the full test suite. On pass: measure new LOC, compute
  the delta, print the iteration summary. On fail: revert patches in **reverse
  application order** with `git apply -R` (using the logged patch paths) until
  green; mark each reverted change and bump its category's revert counter. If no
  tests exist, run the README/main entry point and note "verified: manual run".
  If granular revert fails, stop and report the touched files and the failed
  command — **never** fall back to whole-tree `git checkout .` / `git reset --hard`
  in a dirty worktree (see `execution-contract.md` → Worktree Safety).
- **Phase 5 — Convergence.** Check stopping conditions in order: **clean**
  (all agents return zero HIGH/MEDIUM on a re-scan), **plateau** (fewer than 2
  changes successfully applied this iteration), **limit** (iteration count reached
  the skill's cap, default 5), **unstable** (a high fraction of this iteration's
  changes reverted — flag for human review), **full quarantine** (every category
  quarantined). If none apply, increment the iteration and return to Phase 1.
- **Phase 6 — Report.** Print iterations completed, starting vs final LOC with
  percentage removed, test pass count (before/after), per-category change counts,
  reverted count, quarantined categories, and remaining items flagged for human
  review. Remind the user all changes are in the working tree — review with
  `git diff` and commit yourself; this skill never commits. End with the
  parseable `DONE:` line.

## Quarantine (optional, per skill)

A change category (e.g. `bug`, `simplify`, `arch`, `security`) enters quarantine
when its cumulative revert rate exceeds 50% over a meaningful sample (attempted
≥ 4 to avoid flukes). Once quarantined, all findings in that category are skipped
for the rest of the run and a warning is printed. This stops a skill from
repeatedly applying and reverting the same kind of risky change. shrinkray does
not enable quarantine; code-smellz does.

## Finding schema

Each skill defines its own JSON schema in `references/subagent-prompts.md`.
The only field this loop mandates is `patch` — a unified-diff hunk applicable
with `git apply`, or `null` when the change is too complex for a patch (then the
orchestrator applies it manually from the description).

## Gates each skill opts into

| Gate | code-smellz | shrinkray |
|---|---|---|
| Static-analysis pre-pass (`static_analysis.py` / `deadcode_scan.py`) | yes | yes |
| Type-check / lint / format gates (Phase 4) | yes | yes |
| CVE / dependency audit (Phase 0) | yes | no |
| Quarantine | yes | no |
| Second minimizer pass (Phase 3.3) | yes | yes |
| Propose-then-implement for structural roles (Phase 1.5) | no | yes |
| Whole-file "ghost file" deletion | no | yes |

Skills add their opted gates inline where the loop above says "skill-specific";
they do not duplicate the skeleton.
