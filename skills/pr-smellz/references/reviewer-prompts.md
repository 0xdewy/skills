# PR Reviewer Lenses

Load the common contract and only the selected lenses. Each lens may read only
`<WORKSPACE>/evidence-pack.md`. It returns one JSON object in its final message.
The parent writes that object to the owned path. A lens does not write files,
search the repo, edit, or comment on the PR.

## Common Contract

Every finding must:

- identify behavior or complexity introduced or materially worsened by this diff;
- anchor `path`, `line`, and `side` to an added, modified, or removed line;
  `side` is `old` or `new`;
- cite concrete code or data-flow evidence and user or system impact;
- include a focused verification command, trace, or test idea;
- use `critical | high | medium | low` severity and `high | medium` confidence.

Return this object:

```json
{"findings": [], "evidence_requests": []}
```

`findings: []` with `evidence_requests: []` means the lens assessed the pack.
A request means the pack cannot support that point. Request fields are
`{id, path, need, why}`, specific enough to quote one revision-pinned excerpt.
Do not turn missing context into a finding. Exclude style preferences,
pre-existing defects, and missing-test complaints without a plausible
regression path. Correctness owns that missing-test case.

## Pareto Lens (Highest Priority)

Favor subtraction over addition and simplicity over complexity. Question whether
new requirements are necessary to the stated goal before reviewing how they are
implemented. Look for unnecessary scope, duplicate code or sources of truth,
speculative abstractions or configuration, redundant dependencies, and systems
whose coordination or maintenance cost exceeds the value of the changed behavior.

For each finding, name what to delete, collapse, or reuse; show the concrete cost
it introduces and why the smaller solution still satisfies the goal. Verify
callers and contracts before declaring code redundant. Fewer lines alone are not
evidence: reject cosmetic preferences and simplifications that merely hide or
move complexity. Use empty findings when the added complexity is justified.

Challenge an explicit requirement openly as a proposed scope change, explaining
the benefit lost and why removal is worthwhile; do not silently discard it or
remove it under `--fix` without user agreement. Preserve required correctness and
security safeguards. Keep every proposal anchored to the diff, not whole-repo
cleanup. Product owns what callers and operators experience. Maintainability
owns code that should exist but is harder to change. This lens owns whether the
added machinery needs to exist at all.

Parent writes: `findings-pareto.json` (schema lens: `pareto`).

## Correctness Lens

Look for broken invariants, edge cases, error-path regressions, incorrect state
transitions, concurrency or order problems, resource leaks, and behavior that
contradicts the PR description or existing tests or contracts.

Parent writes: `findings-correctness.json` (schema lens: `correctness`).

## Product Lens

Look for what a user, API caller, or operator will experience. This lens owns
incompatible caller-visible API, schema, or config changes; migration and
rollback hazards; and operational failure modes. UI, copy, CLI, and workflow
changes count when the diff makes that experience worse or impossible. Ignore
subjective visual preference.

Parent writes: `findings-product.json` (schema lens: `product`).

## Maintainability Lens

Look for code the diff needs that is harder to maintain than the behavior
requires: duplication, extra wrappers, tangled branching, and indirection
introduced here. Name the concrete maintenance cost. Ignore style and whole-repo
cleanup. Existence of the machinery belongs to Pareto.

Parent writes: `findings-maintainability.json` (schema lens: `maintainability`).

## Security And Boundary Lens

Look for a weakened or removed safeguard, a changed trust boundary,
authorization or authentication mistakes, injection, unsafe parsing,
sensitive-data exposure, dependency or configuration hazards, and missing
validation at newly reachable inputs. A removed guard needs no new boundary.
Do not audit unchanged code.

Parent writes: `findings-security.json` (schema lens: `security`).
