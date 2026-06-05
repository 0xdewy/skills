# Auto Memory Integration Guide

Loaded by agentify during Phase 3 (Design) to understand how auto memory
interacts with the generated doc hierarchy.

---

## What Auto Memory Is

Claude Code maintains auto memory at:
```
~/.claude/projects/<project>/memory/MEMORY.md
```

This file is **Claude-managed**. Claude reads and writes it during sessions.
The first 200 lines (or 25KB, whichever comes first) are loaded into context
at the start of every session.

The skill **never writes** to auto memory. It detects and accounts for it.

---

## How Auto Memory Affects Generated Docs

### The Duplication Problem

If auto memory already contains:
- Build commands → don't include them in CLAUDE.md (just reference: "see auto memory")
- Debugging patterns Claude learned → don't repeat them in CLAUDE.md
- Code style preferences Claude inferred → don't restate them in CLAUDE.md

Duplication wastes the ~8,000-token startup budget. CLAUDE.md and auto memory
are read back-to-back at session start.

### The Complement Strategy

Generated docs should **complement** auto memory, not compete with it:

| Auto memory already knows | CLAUDE.md should provide |
|--------------------------|-------------------------|
| Build command learned from trying `npm run build` | Explicit test command: `npm run test -- --coverage` |
| "Always use 2-space indentation" | "Python: 4 spaces (black default)" |
| Debugging pattern: "check logs at /var/log/app" | Architecture: "Logs are structured JSON → see docs/OVERVIEW.md" |

### Detection Output

When `analyze_repo.py` detects auto memory, it outputs in the analysis summary:
```
Auto memory:  found (45 lines at ~/.claude/projects/my-project/memory/MEMORY.md)
Auto memory:  not found
```

The LLM generating CLAUDE.md should:
1. Read the auto memory file (if found)
2. Check for overlapping content
3. Only include information in CLAUDE.md that auto memory doesn't already have
4. Add a short note: "<!-- Auto memory at ~/.claude/projects/.../memory/MEMORY.md contains session-learned information. -->"

---

## When Auto Memory Conflicts With CLAUDE.md

If auto memory says one thing and CLAUDE.md says another:
- CLAUDE.md takes priority (user-written > Claude-inferred)
- But the conflict itself should be noted in CLAUDE.md:
  "IMPORTANT: Use npm not yarn (auto memory may suggest yarn from prior sessions)"
