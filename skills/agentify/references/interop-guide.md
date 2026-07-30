# Interoperability Guide: AGENTS.md, .cursorrules, .windsurfrules

Loaded by agentify during Phase 3 (Design) when one of these files is
detected in the repository.

---

## AGENTS.md

If `AGENTS.md` exists at the repo root, Claude Code can use it. In fact,
`/init` in Claude Code **reads AGENTS.md** when generating a CLAUDE.md.

### Pattern: Import AGENTS.md

The cleanest approach is to create CLAUDE.md that imports AGENTS.md:

```markdown
@AGENTS.md

## Claude Code

- Use plan mode for changes under `src/billing/`
- Run `npm run typecheck` after any TypeScript change
```

This way:
1. AGENTS.md serves both Claude Code AND other coding agents
2. Claude-specific instructions live below the import
3. No duplication between AGENTS.md and CLAUDE.md
4. `/init` can build on this structure automatically

### Pattern: Symlink

If no Claude-specific content is needed:

```bash
ln -s AGENTS.md CLAUDE.md
```

On Windows, prefer the import pattern (symlinks require admin/Developer Mode).

---

## .cursorrules

Cursor's `.cursorrules` file serves a similar purpose to CLAUDE.md. If found:
- Detect and mention it in the analysis summary
- Cursor-specific rules (like @Docs, @Web) don't apply to Claude Code
- General coding conventions from .cursorrules can be migrated to CLAUDE.md
- Suggest: "You have both .cursorrules and a CLAUDE.md being generated. Consider
  consolidating shared conventions into one source."

---

## .windsurfrules

Similar to .cursorrules. If found:
- Detect and mention in analysis summary
- Suggest consolidation into a single AGENTS.md (then have both CLAUDE.md and
  other tools import from it)

---

## Decision Matrix

| Situation | Recommended approach |
|-----------|---------------------|
| Only AGENTS.md exists | CLAUDE.md imports it with `@AGENTS.md` |
| AGENTS.md + .cursorrules exist | Create CLAUDE.md importing AGENTS.md; mention .cursorrules in analysis |
| Only .cursorrules exists | Extract general conventions to CLAUDE.md; add @import for shared parts |
| Multiple agent configs with overlapping rules | Suggest creating AGENTS.md as canonical source; import from all |
| No prior agent configs | Standard agentify generation from scratch |

---

## Detection in analyze_repo.py

The script detects:
- `AGENTS.md` → `has_agents_md: true` in analysis.json
- `.cursorrules` → listed in `existing_docs` if present
- `.windsurfrules` → listed in `existing_docs` if present

When detected, the Phase 3 design plan should mention interoperability options.
