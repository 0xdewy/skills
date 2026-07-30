# Template Syntax Reference

Loaded by agentify during Phase 4 when filling any file in `templates/`.

Templates use double-brace placeholder notation:

---

## 1. Simple Replacement

`{{project_name}}` → replace with the literal value from analysis.json.

Examples:
- `{{project_name}}` → `my-service`
- `{{date}}` → `2026-05-28`
- `{{build_command}}` → `npm run build`

---

## 2. Conditional Block

`{{optional_X: ...content...}}`

Include the inner content if condition X applies; delete the entire block
(including outer braces) if it does not.

Examples:
- `{{optional_ag_import_if_agents_md_exists: @AGENTS.md}}` — included only if
  `has_agents_md` is true in analysis.json
- `{{optional_coordination_section: ## Agent Coordination\n...}}` — included
  only when coordination dirs were created in Phase 4.7
- `{{optional_imports_if_large_claude_md: @.claude/commands.md}}` — included
  only if CLAUDE.md draft exceeds 160 lines

---

## 3. Repeat Block

`{{items_format:\n  row template\n}}`

For each item in the corresponding list from analysis.json, emit one copy of
the inner template with its placeholder values filled in. If the list is empty,
delete the entire block.

Examples:
- `{{component_rows_format:\n| {{Component name}} | docs/{{slug}}.md |\n}}`
  → one row per entry in `component_dirs`, with name and lowercased slug
- `{{rules_rows_format:\n- {{Domain}} → .claude/rules/{{domain}}.md\n}}`
  → one row per entry in `existing_rules`

---

## Cleanup Rule

After filling all placeholders, scan the output for any remaining `{{` or `}}`
strings and delete them (they represent unfilled optionals or empty lists).
The output file must not contain any `{{` or `}}` characters.
