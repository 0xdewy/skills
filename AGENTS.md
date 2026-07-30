# Codex Guidance

## Repository Purpose

This repository authors and tests Codex-compatible agent skills. The canonical
skill sources live in `skills/*/SKILL.md` with optional `references/`, `scripts/`,
`evals/`, `templates/`, and `memory/` subdirectories.

Codex discovers installed copies through user skill locations such as
`~/.codex/skills` and `~/.agents/skills`. The repo root `.agents/` directory may
be read-only in managed environments, so do not assume it can be edited.

## What To Read

- For a skill change, read that skill's `SKILL.md` first.
- Read referenced files only when the selected skill points to them for the
  current task.
- Use `skills/common/` for shared guidance that affects multiple skills.
- Use `evals/evals.json` when changing triggers, output contracts, safety rules,
  or behavior that should be tested.

## What To Ignore

Do not inspect or summarize these unless the user explicitly asks about local
tooling, caches, or runtime state:

- `.venv/`
- `.pytest_cache/`
- `**/__pycache__/`
- `**/*.pyc`
- `.claude/settings.local.json`
- `skills/**/.claude/settings.local.json`
- `skills/*/learnings/`
- generated reports, temporary workspaces, and cache directories

Do not read `skills/*/memory/memory.jsonl` unless the active task is explicitly
about that memory skill or the user asks to inspect saved memories. Treat memory
files as persisted user data, not as ordinary source docs.

## Safety

- Never use whole-tree destructive recovery commands such as `git reset --hard`,
  `git checkout .`, or broad `git restore .`.
- Preserve unrelated worktree changes. This repo is often dirty during skill
  development.
- Prefer patch-scoped edits and reversions.
- Do not add bypass, evasion, credential-harvesting, or access-control
  circumvention instructions to skills.

## Verification

For broad skill edits, run at least:

```bash
python3 - <<'PY'
import json, pathlib
for p in pathlib.Path('skills').glob('*/evals/evals.json'):
    json.loads(p.read_text())
print('eval json ok')
PY
```

For shell scripts, run `bash -n path/to/script.sh`. For Python scripts, prefer
`ast.parse` over `py_compile` so verification does not create `__pycache__/`.
