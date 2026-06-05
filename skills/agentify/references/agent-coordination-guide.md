# Agent Coordination Directories

agentify can scaffold `docs/plans/`, `docs/specs/`, and `docs/reviews/` to
create a coordination layer for multi-agent repos. This guide explains when
to create them, what they're for, and how agentify manages them.

---

## When to Create Coordination Dirs

Create these directories when **either** condition is true:

1. **Multi-agent signals detected** by `analyze_repo.py`:
   - `has_agents_md: true` (AGENTS.md exists in repo root)
   - `.claude/agents/` directory exists
   - `project_type` is `agent-skill` or `monorepo`
   - `docs/plans/` or `docs/specs/` already exist (prior manual creation)

2. **User explicitly requests them** via trigger phrases:
   - "set up coordination docs", "create docs/plans", "agent coordination hub",
     "create plans/specs/reviews", "set up agent coordination"

If neither condition is met: mention coordination dirs as an **optional** item
in the Phase 3 plan printout. Wait for user to confirm before creating them.
Do not create empty scaffolding by default for single-developer repos.

---

## What Each Directory Is For

### docs/plans/ — Implementation Plans
Work items that an agent (or developer) can pick up and execute. A plan file
describes: what to build, why, the acceptance criteria, and the steps. Plans
are consumed by implementer/builder agents. Status lifecycle:
`draft → ready → in-progress → blocked → complete`

### docs/specs/ — Specifications
Source-of-truth contracts before implementation. An agent working from a spec
must not deviate without updating the spec first. Spec files describe: what
the system must do, the public interface, constraints, and open questions.
Status lifecycle: `draft → review → approved → implemented → deprecated`

### docs/reviews/ — Review Findings
Historical record from code reviews, design reviews, and security audits.
Read-only reference for future agents: "what was wrong here before, what was
decided." Filing a review here makes its findings persistent across sessions.
Status lifecycle: `open → addressed | wont-fix`

---

## Ownership Boundary

**agentify owns:**
- `docs/plans/README.md` — the stub explaining the directory (≤80 lines)
- `docs/specs/README.md` — same
- `docs/reviews/README.md` — same

**agentify never touches:**
- Any `*.md` file that is not named `README.md` in these directories
- These files are agent/developer work artifacts and must never be overwritten

When auditing (Phase 2), agentify scores the README stubs with `audit_context.py`.
It reports artifact file counts but does not modify or score individual plan/spec/
review files.

---

## Wiring into CLAUDE.md and context-map.md

After creating coordination dirs (Phase 4.7), add to CLAUDE.md navigation table:

```markdown
| Implementation plans | docs/plans/ |
| Feature specs        | docs/specs/ |
| Review findings      | docs/reviews/ |
```

Add to `.claude/context-map.md` under a new "Agent Coordination" section:

```markdown
## Agent Coordination

- Implementation plans for agents to pick up → `docs/plans/`
- Feature and API specifications → `docs/specs/`
- Code and design review findings → `docs/reviews/`
```

Only add these entries if the directories were actually created. Never add
dead pointers pointing to non-existent directories.

---

## Token Budget Note

The README stubs (`docs/plans/README.md` etc.) are **not** auto-loaded —
they are on-demand reference files. They do not count against the CLAUDE.md
200-line budget. The CLAUDE.md navigation rows that point to these dirs are
typically 3 lines total — negligible budget impact.

---

## Audit Rubric for Coordination Dirs

Scored by `audit_context.py` using `audit_coordination_dir()`:

| Criterion | Points |
|-----------|--------|
| README.md exists and is ≤80 lines | 30 |
| README.md has an "example" or "template" section | 30 |
| At least one artifact file exists (active use) | 20 |
| Artifact files have frontmatter with title/status | 20 |

Score interpretation: >80 → keep; 60-80 → improve; <60 → regenerate README stub.
Never regenerate artifact files regardless of score.
