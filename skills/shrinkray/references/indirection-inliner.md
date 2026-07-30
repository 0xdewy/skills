# Indirection Inliner

Propose-then-implement: identify indirection layers that no longer earn their
cost and propose inlining + deletion. Cross-file aware.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`; cross-file index `{{dependency_index_path}}`.

The pre-built `dependency_index.json` is your authoritative source for the
single-caller and single-implementor candidates. Pull from:

- `single_caller_symbols` — symbols with exactly one external call site.
  Each is an inlining candidate. The index already tells you the sole
  caller's file and line.
- `single_implementor_interfaces` — interfaces/abstract bases with exactly
  one implementor. Inline the implementor's logic into the interface's
  callers and delete both, or collapse the abstraction.

Also examine (less reliably — these need your judgment):

- Pass-through functions whose body is `return self._x.f(...)` or
  `return delegate(...)` — wrappers that add no transformation.
- Single-caller wrapper classes that exist only to hold configuration the
  caller already has.
- Adapter layers where the adapter and adaptee have converged over time.
- Builders with only one realistic built configuration.

For each candidate: cite the index entry or the specific code you observed,
include the patch that inlines the body at the call site and deletes the
definition, and confirm tests still cover the inlined behavior. Set
`source_tool: "dependency_index"` when the candidate came from the index;
`source_tool: null` for manually discovered ones. `confidence: medium` is
the right default — inlining is a behavior-preserving but readability-affecting
change.

Skip cases where the indirection is intentional (plugin interface, future
expansion explicitly documented, dependency-injection boundary, public API).
Follow `references/common-findings.md`, use `category: "consolidate"`, and
write `{{output_path}}`.
