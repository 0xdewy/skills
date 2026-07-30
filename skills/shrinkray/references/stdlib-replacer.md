# Stdlib Replacer

Propose-then-implement: identify hand-rolled reimplementations of stdlib or
already-imported library functions, then write patches that delete the
hand-rolled version and route callers to the canonical one.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`; cross-file index `{{dependency_index_path}}`.

Hunt for:

- Custom implementations of stdlib helpers (`any`, `all`, `sum`, `groupby`,
  `chain`, `partial`, `lru_cache`, `dataclasses`, `collections.defaultdict`,
  `pathlib` operations, `itertools` recipes, `more_itertools` when imported).
- Custom implementations of well-known library functions when the library is
  already a project dependency (lodash for JS, functools/itertools for Python,
  `strings`/`slices`/`maps` for Go, `itertools` for Rust).
- Hand-rolled serialization, validation, retry, or parsing loops that a
  one-line library call replaces.
- Type/class hierarchies that exist only to namespace a few static methods —
  candidates for module-level functions or `@staticmethod` collapse.

For each candidate: state what the hand-rolled version does, name the exact
stdlib/library function that replaces it, cite the canonical signature, and
include the patch that removes the hand-rolled version and updates callers.
Set `source_tool: null` (LLM-discovered, not tool-certified) and
`confidence: medium` unless you can show behavioral equivalence with a quick
test.

Follow `references/common-findings.md`, use `category: "verbosity"` (the
category is "smaller equivalent"), and write `{{output_path}}`.
