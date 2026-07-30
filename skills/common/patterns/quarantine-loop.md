# Quarantine Loop Pattern

Shared converge-and-revert loop for read-only-agent cleanup skills:
`code-smellz` and `shrinkray`. Both run the same six-phase skeleton — they differ
only in agent roster, finding schema, and which gates they enable. Load this
alongside `execution-contract.md` (patch-only rollback, `DONE:` signal) and
`workspace.md` (scratch directory resolution). Each skill defines its own agents
and output schema in its `references/subagent-prompts.md`; this file is the loop
they both run.

## Contract summary

- **Phase 0 — Setup & baseline.** Resolve a scratch workspace (see `workspace.md`).
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
  (`git diff > pre-iter-N.diff`). Apply in the skill's dependency order
  (shrinkray: ghost files → dead code → consolidation → verbosity; code-smellz:
  security first, then shared-utility bugs, file bugs, architecture, simplify).
  For each finding: if it has a `patch`, `git apply --check` then `git apply`;
  if `--check` fails (file changed since the agent read it), fall back to a manual
  edit from the description. **After each individual change**, run the cheapest
  available correctness check (type checker, or `py_compile` for Python) and
  `git apply -R` that single patch immediately if it introduces new errors. Log
  every applied change to `session.json → history` with its patch path so revert
  is O(1).
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

Each skill's `references/subagent-prompts.md` defines its own JSON schema
(code-smellz uses `severity`/`type`; shrinkray uses `confidence`/`category`).
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
| Whole-file "ghost file" deletion | no | yes |

code-smellz uses `static_analysis.py` (dead code + dupes + tool detection).
shrinkray uses its own `deadcode_scan.py`, which wraps language-native
dead-code tools (vulture, knip, golang.org/x/tools/cmd/deadcode, cargo-udeps)
plus type-checker unused-symbol diagnostics into one unified findings JSON.
LLMs are weak at *discovering* dead code by reading (SmellBench arXiv:2606.05574,
best agent at ~50% smell elimination, failure mode is local focus and missing
cross-file refs); language-native AST tools are 100-1000x more effective in
practice. The Dead Code Hunter and Ghost File Hunter agents verify-and-apply
tool-flagged candidates rather than discover.

Skills add their opted gates inline where the loop above says "skill-specific";
they do not duplicate the skeleton.

## Phase 3.3 — Second minimizer pass

After a patch lands and passes the per-change syntax check, re-read the
*result* and ask whether it can be shrunk further now that constraints have
shifted. This catches two patterns the original agent could not:

- A consolidation introduces a helper; the helper itself is now a candidate
  for inlining, stdlib replacement, or further simplification.
- Removing dead code makes adjacent code dead (the canonical advice from
  vulture's docs: *"After you have found and deleted dead code, run Vulture
  again, because it may discover more dead code"*).

For shrinkray: re-run `deadcode_scan.py` on the affected file(s) after each
successful apply; if it emits new findings for the same file, feed those back
into Phase 2 as additional candidates in the same iteration. This is bounded
by the iteration cap and the convergence gate.

## Phase 1.5 — Propose-then-implement decomposition (structural roles only)

CodeTaste (arXiv:2603.04177) shows LLMs implement specified refactorings well
but discover them poorly, and that a *propose-then-implement* decomposition
improves alignment with the right change. shrinkray applies this to its
**structural roles** (Code Consolidator, Stdlib Replacer, Indirection Inliner,
Table-Drive Converter, Flag Pruner, Module Merger). The verify-and-apply
primary roles (Dead Code Hunter, Ghost File Hunter) skip this — they have a
tool-certified candidate already and go straight to patches.

For each structural role the orchestrator dispatches:

1. **Propose pass** — the agent reads its slice + `dependency_index.json`,
   writes a proposal file at `{{proposal_path}}` containing one entry per
   candidate: `{file, lines, current_approach, suggested_approach,
   estimated_loc_saved, confidence, risks}`. No patches yet.
2. **Selection** — the orchestrator reads all proposals, drops candidates
   with negative or sub-5 LOC net savings, drops candidates whose risks
   column flags public-API or test-coverage concerns, and ranks the rest.
3. **Implement pass** — re-dispatch the same role with the proposal file
   plus an instruction to produce unified-diff patches for the top N
   candidates only. The agent writes its `{{output_path}}` findings JSON
   in the standard schema.

This avoids the failure mode where an agent invests in a patch for a
candidate that should have been filtered out at the proposal stage. The
selection step is the orchestrator's responsibility (single-writer rule).
