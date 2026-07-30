# Falsification Methods

Choose the cheapest method capable of distinguishing the candidate from a
nearby false property. Combine methods only when they cover different risks.

| Method | Use when | Minimum record |
|---|---|---|
| Boundary/exhaustive | Domain is small or partitions are known | Values/partitions and case count |
| Property-based | Inputs can be generated and the oracle is direct | Generator constraints, seed, cases, shrink result |
| Metamorphic | Correct output is hard to know but transformations are meaningful | Source input, transformation, expected relation |
| Differential | A trusted implementation/version/encoding exists | Oracle identity, normalization, mismatch |
| Stateful/model-based | Correctness depends on operation sequences | Initial state, command generator, model, minimal sequence |
| Fuzz | Parser/protocol surface accepts large byte or token spaces | Corpus, seed, time/case limit, crash/hang policy |

## Candidate Patterns

- **Closure/bounds:** output remains in the documented domain.
- **Idempotence:** `f(f(x)) == f(x)` where normalization is intended.
- **Round trip:** `decode(encode(x)) == normalize(x)`.
- **Inverse:** `undo(do(x)) == x` within stated preconditions.
- **Order relation:** monotonicity or stable ordering under an ordered input.
- **Permutation/duplication:** reorder or duplicate irrelevant inputs without
  changing the observation.
- **Conservation:** value, count, or ownership changes only through named
  transitions.
- **Isolation:** an operation on A cannot affect unrelated B.
- **Failure atomicity:** rejected operations leave observable state unchanged.
- **Representation equivalence:** alternate encodings or implementations agree
  after normalization.

These are prompts for investigation, not assumed truths.

## Selection Rules

1. Partition invalid inputs separately; never silently redefine "valid" to
   exclude a counterexample.
2. Use repository-native tooling first: Hypothesis, fast-check, proptest,
   QuickCheck, jqwik, ScalaCheck, Hedgehog, or the existing fuzz harness.
3. Without a property framework, write deterministic table/exhaustive loops in
   the native test runner. Do not add a dependency without permission.
4. Treat a differential oracle as fallible. Record why it is authoritative and
   compare only normalized observable behavior.
5. For stateful tests, include invalid operations, repeated operations, and
   interruption boundaries when the API defines them.
6. Shrink semantically: fewer operations, smaller collections, simpler Unicode,
   lower magnitudes, and fewer state transitions. Preserve the failure.
7. Store a failing seed *and* the minimized concrete example; seeds alone may
   stop reproducing after generator changes.
8. Capture command output before summarizing it; record exit code, executed case
   count, duration, SHA-256 digest, and the minimized replay command.

## Quality Rejections

Reject candidates that are:

- tautological or guaranteed by the test generator;
- a direct copy of implementation logic used as its own oracle;
- true only for the examples already present;
- dependent on unspecified ordering, timing, randomness, or formatting;
- an observed quirk being mislabeled as intended behavior;
- too broad to falsify within a bounded command.
