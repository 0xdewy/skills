# PR Reviewer Lenses

Load the common contract and only the selected lenses. Each reviewer reads the
merge-base diff plus minimal task-local context and writes one JSON array to its
owned path. Reviewers never edit, comment on the PR, or inspect unrelated code.

## Common Contract

Every finding must:

- identify behavior or complexity introduced or materially worsened by this diff;
- anchor `path` and `line` to an added or modified line;
- cite concrete code/data-flow evidence and user or system impact;
- include a focused verification command, trace, or test idea;
- use `critical | high | medium | low` severity and `high | medium` confidence.

Return `[]` when no actionable findings exist. Exclude style preferences,
pre-existing defects, claims based only on a hunk without reading necessary
context, and missing-test complaints without a plausible regression path.

## Pareto Lens (Highest Priority)

Favor subtraction over addition and simplicity over complexity. Question whether
new requirements are necessary to the stated goal before reviewing how they are
implemented. Look for unnecessary scope, duplicate code or sources of truth,
speculative abstractions/configuration, redundant dependencies, and systems whose
coordination or maintenance cost exceeds the value of the changed behavior.

For each finding, name what to delete, collapse, or reuse; show the concrete cost
it introduces and why the smaller solution still satisfies the goal. Verify
callers and contracts before declaring code redundant. Fewer lines alone are not
evidence: reject cosmetic preferences and simplifications that merely hide or
move complexity. Return `[]` when the added complexity is justified.

Challenge an explicit requirement openly as a proposed scope change, explaining
the benefit lost and why removal is worthwhile; do not silently discard it or
remove it under `--fix` without user agreement. Preserve required correctness and
security safeguards. Keep every proposal anchored to the diff, not whole-repo
cleanup. The API/design/tests reviewer owns compatibility and integration risks;
this reviewer owns whether the added machinery needs to exist at all.

Owned output: `findings-pareto.json` (schema lens: `pareto`).

## Correctness Lens

Look for broken invariants, edge cases, error-path regressions, incorrect state
transitions, concurrency/order problems, resource leaks, and behavior that
contradicts the PR description or existing tests/contracts.

Owned output: `findings-correctness.json`.

## Security And Boundary Lens

Look for changed trust boundaries, authorization/authentication mistakes,
injection, unsafe parsing, sensitive-data exposure, dependency/config hazards,
and missing validation at newly reachable inputs. Do not perform a broad
security audit of unchanged code.

Owned output: `findings-security.json`.

## API, Design, And Tests Lens

Look for incompatible public API/schema/config changes, migration/rollback
hazards, integration coupling, operational failure modes, and missing tests for
specific changed behavior. Ignore subjective architecture preferences unless
the diff creates a concrete maintenance or reliability failure.

Owned output: `findings-design-tests.json`.
