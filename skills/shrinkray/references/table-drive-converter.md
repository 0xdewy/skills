# Table-Drive Converter

Propose-then-implement: identify switch/if-else ladders and near-identical
function families that collapse to data-driven dispatch, then write the
patch.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`; cross-file index `{{dependency_index_path}}`.

Hunt for:

- `switch`/`if-elif` chains over a small fixed key where each branch runs
  near-identical logic with different parameters. Replace with a dict from
  key → parameter struct (or key → callable). Net win = N branches collapse
  to one dispatch + a table.
- Families of near-identical functions (`handle_create`, `handle_update`,
  `handle_delete`) that differ only in which fields they touch — collapse
  into one parameterized function.
- Repeated try/except wrappers around different calls with the same handler
  body — extract a wrapper.
- Long sequences of `if x == 'a': ... elif x == 'b': ... elif x == 'c': ...`
  used to translate constants — replace with a lookup table.

For each candidate: show the current ladder (lines + count of branches),
show the proposed table + dispatch, and write the patch. The patch often
*adds* a small table to *remove* many lines — that is correct; report the
net LOC saved honestly in `estimated_loc_saved`. Net savings must be
positive; skip candidates where the table is not clearly smaller.

Set `source_tool: null` (LLM-discovered). `confidence: medium` for clear
wins; `low` when the dispatch table would obscure behavior or the branches
are diverging. Follow `references/common-findings.md`, use
`category: "consolidate"`, and write `{{output_path}}`.
