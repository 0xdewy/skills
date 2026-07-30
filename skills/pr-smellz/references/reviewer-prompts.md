# PR Reviewer Lenses

Load the common contract and only the selected lenses. Each reviewer reads the
merge-base diff plus minimal task-local context and writes one JSON array to its
owned path. Reviewers never edit, comment on the PR, or inspect unrelated code.

## Common Contract

Every finding must:

- identify behavior introduced or materially worsened by this diff;
- anchor `path` and `line` to an added or modified line;
- cite concrete code/data-flow evidence and user or system impact;
- include a focused verification command, trace, or test idea;
- use `critical | high | medium | low` severity and `high | medium` confidence.

Return `[]` when no actionable findings exist. Exclude style preferences,
pre-existing defects, claims based only on a hunk without reading necessary
context, and missing-test complaints without a plausible regression path.

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
