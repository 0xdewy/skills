---
name: invariant-miner
description: >-
  Mines evidence-backed invariants and falsifies them with generative
  tests, shrinking reproducible counterexamples. Only use when explicitly
  requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 1.0.0
  category: testing
  activation: explicit
  tags:
    - invariants
    - property-testing
    - fuzzing
    - testing
    - counterexamples
---

# Invariant Miner

Discover general behavioral properties, then attempt to disprove them with
executable tests. A plausible statement is a candidate, not an invariant.

Load `../common/patterns/execution-contract.md` and
`../common/patterns/scaling.md`. Consult
`../common/ROUTING.md` for overlap. Load `references/methods.md` only when
selecting a falsification technique. Use `scripts/validate_ledger.py` before
completion.

## Activation

Use this for *general properties over an input or state space*. Add one known
example test directly without this skill. Route broad bug/quality cleanup to
`code-smellz` and diff-scoped review to `pr-smellz`.

Edit authority follows the request:

- Discovery/review request: production and durable test files are read-only;
  probes stay in `WORKSPACE`.
- Add/encode/test request: tests may be edited, but production code is read-only.
- `--fix`: after a counterexample exists, apply the smallest production fix and
  rerun the new test plus the relevant suite.

Never commit, push, install dependencies, or expand the target without explicit
permission.

## Modes

- `--quick`: one function/type; 3-5 candidates, one primary method.
- `--standard` (default): one subsystem; 5-12 candidates, up to three methods.
- `--thorough`: a public API or state machine; at most 20 candidates, bounded
  combinations of methods.

All modes run directly with zero subagents. Set deterministic seeds and bounded
case/time limits; record both. Existing property-test libraries are preferred,
but a small native loop is the fallback.

## Evidence Contract

Write each candidate as: **for all valid inputs/states satisfying P, observation
Q holds**. Record its basis:

- `contract`: explicit schema, requirement, public documentation, or accepted
  test contract.
- `derived`: follows from types, algebra, state transitions, or at least two
  independent repository signals.
- `observed`: current implementation behavior only; characterization, not
  intended correctness.

Do not promote naming, one example, or implementation coincidence into a
durable test. Conflicting sources make the candidate `blocked` until authority
is resolved. Durable tests may encode `contract` and well-supported `derived`
invariants; encode `observed` behavior only when the user accepts it as policy.

## Workflow

1. State mode/workspace. Record target, edit authority, baseline, seed, and
   budgets in `status.json`.
2. Read repo guidance, test configuration, target code, direct callers, existing
   tests, and authoritative schemas/docs. Keep scope local.
3. Draft and rank candidates by basis, evidence strength, failure impact, and
   falsifiability. Reject tautologies, exact restatements, and properties that
   merely mirror one implementation branch.
4. Choose the cheapest discriminating method from `references/methods.md`.
   Prefer boundary partitions before random volume.
5. Write probes in `WORKSPACE`, or durable tests only when authorized. Run the
   narrowest command first. Preserve the baseline distinction.
6. On failure, reproduce with the recorded seed and shrink to the smallest
   input or operation sequence. A non-reproducible failure is `blocked`, not a
   counterexample.
7. Classify each candidate. For executed results record exit code, case count,
   duration, output SHA-256, and a replay command for counterexamples. Passing
   finite trials means "not falsified within this budget," never proof.
8. Run `scripts/validate_ledger.py --print-template`, write `INVARIANTS.json`
   from that schema, then `REPORT.md` with supported properties,
   counterexamples, test changes, commands, budgets, and residual search gaps.
9. Run the ledger validator and all targeted tests. With `--fix`, also run the
   relevant regression suite after the production patch.

Do not weaken assertions to make generated tests pass. Never expose secrets or
production data in seeds, corpora, ledgers, or counterexamples.

Final line:

```text
DONE: <WORKSPACE>/REPORT.md — <S> supported, <F> falsified, tests <added|unchanged>, verification <passed|partial|blocked>
```
