---
name: spec-reconciler
description: >-
  Reconciles source-anchored claims across schemas, code, tests, docs, and
  generated clients using declared authority. Only use when explicitly
  requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 1.0.0
  category: quality
  tags:
    - specifications
    - contracts
    - schemas
    - documentation
    - drift
---

# Spec Reconciler

Turn competing repository artifacts into atomic, source-anchored claims and
classify their disagreements without inventing a source of truth.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`; consult `../common/ROUTING.md` for overlap.
Use `references/claim-model.md` and `scripts/reconcile_claims.py` when extracting
and classifying claims.

## Activation

Use only when at least two artifacts make claims about the same external or
developer-visible behavior. For properties over input/state spaces, use
`invariant-miner`; for one known documentation correction, edit directly.

Default is report-only. `--fix` may update a surface only when all are true:

1. repository evidence establishes one unique authoritative value;
2. the target surface is declared `derived`;
3. its `edit_strategy` is `patch` or `regenerate`;
4. the reconciler marks the conflict `fixable`.

Use the recorded generator for `regenerate`; never hand-edit generated output.
Inspect a recorded command before running it; provenance is not execution trust.
Primary and observed surfaces remain read-only even with `--fix`. Never commit,
push, install dependencies, or broaden scope without explicit permission.

## Modes

- `--quick`: one operation, 2-3 surfaces, at most 20 claims; select it
  automatically for one report-only key.
- `--standard` (default): one API/module, 3-6 surfaces, at most 100 claims.
- `--thorough`: one public contract with clients/examples, at most 10 surfaces
  and 300 claims.

All modes run directly with zero subagents. Scope by operation or claim prefix,
not whole-file ingestion when artifacts are large.

For auto-quick, cite authority and claims, classify inline, and stop: no status,
ledger, or workspace. Use the full workflow for multiple keys, fixes, unclear
extraction, intra-surface conflicts, or a requested durable report.

## Authority Contract

Authority must come from repository guidance, build/generation configuration,
an explicit user decision, or an artifact's generated marker. Record repository
evidence at `path:line`; label explicit user decisions. Freshness, majority
vote, test pass status, file type, and implementation behavior do not establish
authority.

If no policy exists, set `authority_policy.source` to `null` and all ranks to
`null`; disagreements are `ambiguous-authority`. Equal top-ranked conflicting
claims are `authority-conflict`. Do not silently break ties.

## Workflow

For anything beyond the inline quick case:

1. State the mode line, resolve `WORKSPACE`, and write `status.json` with target,
   mode, edit authority, claim/surface budgets, and baseline checks.
2. Inventory only relevant schemas, types, parsers/handlers, tests, docs,
   examples, clients, and generation config. Mark each surface `primary`,
   `derived`, or `observed` with a safe edit strategy.
3. Find authority evidence. If absent, preserve ambiguity. Never infer that a
   generated marker makes the generator's *input* authoritative without repo
   evidence.
4. Run `scripts/reconcile_claims.py --print-template`; extract atomic claims
   using `references/claim-model.md`. Every claim needs a canonical key, JSON
   value, surface, `path:line`, and short evidence statement.
5. Add expectations only where repository evidence says a claim must appear on
   named surfaces. Absence without an expectation is not an omission.
6. Write `CLAIMS.json`, then run:
   `python3 scripts/reconcile_claims.py CLAIMS.json --output CONFLICTS.json`.
   Fix schema errors rather than bypassing the tool.
7. Validate each reported group against its cited lines. Write
   `RECONCILIATION.md` with findings first: intra-surface, ambiguous/authority,
   cross-surface, stale-derived, and omission findings, then consistent scope.
8. With `--fix`, update only tool-marked targets via their recorded strategy.
   Re-extract affected claims and rerun reconciliation plus relevant tests or
   generation checks. A patch alone does not prove drift is resolved.

Do not copy secrets or production payloads into claim values. Normalize only
representation noise documented in `references/claim-model.md`; normalization
must not erase semantic differences.

Final line:

```text
DONE: <WORKSPACE>/RECONCILIATION.md — <C> conflicts, <A> ambiguous, <F> fixed, verification <passed|partial|blocked>
```
