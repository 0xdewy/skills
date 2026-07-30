# Claim Model

A claim is one atomic assertion by one surface about observable behavior. Split
compound schemas and prose so each independently resolvable value has one key.

## Canonical Keys

Use stable, semantic identifiers rather than line numbers:

- `http:POST /users.request.body.email.required`
- `http:GET /users/{id}.response.404.body.code.type`
- `graphql:Mutation.createUser.argument.email.nullable`
- `event:order.created.payload.order_id.format`
- `cli:deploy.option.--region.default`
- `config:server.timeout.unit`

Keep path parameters in canonical brace form. Use schema names only when they
are themselves public; prefer the operation and location a consumer observes.

## Values

Encode values as JSON scalars, arrays, or objects. Normalize only:

- syntactic type aliases proven equivalent in this repository;
- ordering explicitly defined as irrelevant;
- resolved local references when provenance remains recorded;
- formatting that has no consumer-visible meaning.

Do not normalize status codes, nullability, requiredness, defaults, units,
error identifiers, enum membership, cardinality, or ordering semantics.

## Surface Roles

- `primary`: a human-maintained source that cannot be auto-rewritten by this
  skill.
- `derived`: downstream material whose derivation is supported by repository
  evidence; may use `patch`, `regenerate`, or `report-only`.
- `observed`: current runtime or implementation behavior without authority;
  always `report-only`.

Generated output is `derived`, but its input is not automatically authoritative.
Record the policy that establishes ranks separately.

## Extraction Guidance

1. Structured sources first: OpenAPI/JSON Schema, GraphQL SDL, protobuf, types,
   CLI parser declarations, and test assertions.
2. Then implementation branches, generated clients, examples, and prose.
3. Preserve explicit absence (`null`, `false`, empty enum) as a value. Missing a
   claim is different from claiming a null value.
4. Anchor the exact assertion at `path:line`; file-only citations are invalid.
5. Never use the implementation to paraphrase what another surface says.

## Expectations

An expectation states that one key must appear on named surfaces. Add it only
when a generator, policy, public compatibility rule, or explicit user decision
requires that coverage. Otherwise the tool compares claims that exist and does
not speculate about omissions.

## Reading Classifications

- `ambiguous-authority`: no usable policy/rank covers the disagreement.
- `authority-conflict`: top-ranked sources disagree; human decision required.
- `intra-surface-conflict`: one artifact asserts different values for the same
  key; resolve it before cross-surface authority can be applied.
- `cross-surface-conflict`: a unique authoritative value exists, but a
  non-derived surface disagrees; report only.
- `stale-derived`: only lower-ranked derived surfaces disagree.
- `omission`: an explicitly expected surface has no claim for the key.

Only `stale-derived` or `omission` results whose targets are editable derived
surfaces can be marked `fixable`.
