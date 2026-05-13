# Parallel Subagent Patterns

Standard patterns for dispatching multiple subagents simultaneously, collecting
structured output, and merging findings.

---

## Basic Pattern: N Agents, Wait for All

```
Spawn all N agents simultaneously. Each agent:
1. Reads the files it needs (read-only)
2. Writes its findings to a dedicated JSON file
3. Does NOT modify any source files

Wait for ALL agents to complete before proceeding.
```

Each agent gets a focused mandate with:
- A specific lens or question to answer
- An output file path to write to
- The instruction "DO NOT make changes. Read only."

---

## Output Contract

Every parallel agent writes a JSON array to its output file:

```json
[
  {
    "title": "Short action-oriented title",
    "severity": "critical | high | medium | low",
    "effort": "Low | Medium | High",
    "impact": "Low | Medium | High",
    "location": "path/to/file.py:42  (or 'Global')",
    "finding": "What was found. Specific. Cites code or output.",
    "fix": "Concrete suggestion — not vague advice."
  }
]
```

If nothing found, write `[]`. Never write prose — JSON arrays only.

---

## Merging Findings

After all agents complete:

1. Read all output files.
2. **Deduplicate** — if two agents found the same issue (same file+line, same
   root cause), keep the one with the more specific `fix`. Drop the other.
3. **Prioritize** — sort by `severity` descending, then `effort` ascending
   (critical/low-effort first).
4. **Conflict resolution** — if agents disagree (one says keep, one says
   delete), keep the finding from the agent whose mandate is more directly
   relevant to that issue type.

---

## Convergence Criteria (for iterative loops)

Check in this order after each iteration:

1. **Clean** — re-run agents, all return `[]` for HIGH/CRITICAL → stop
2. **Plateau** — fewer than 2 changes successfully applied this iteration → stop
3. **Limit** — iteration count ≥ 5 → stop
4. **Unstable** — >40% of changes this iteration were reverted by tests → stop

If none apply: increment iteration counter and loop back.

---

## Sub-subagent Pattern (coordinator + workers)

When one phase has many independent categories, use a coordinator subagent
that spawns its own child agents:

```
Subagent B (Coordinator):
  Reads the applicable categories from the attack catalog / finding types.
  For each applicable category, spawns a child agent with:
    - The specific category mandate
    - A dedicated output file path (e.g. findings-<category>.json)
  Waits for all children to complete.
  Returns: list of output files written.
```

The top-level caller then merges all output files (from Subagent A, Subagent B's
children, etc.) into the final report.

---

## Progress Tracking with TodoWrite

For skills that use `TodoWrite` for phase tracking:

- When two phases run simultaneously as subagents, mark **both** `in_progress`
  before dispatching.
- When both complete, mark **both** `completed` in a single update.
- Never leave a phase `in_progress` while its agent has already finished.

---

## Completion Signal

**MANDATORY:** Every skill MUST end with a parseable completion line for orchestrators.
Automated pipelines (the `implementer` skill, `loop`-based agents, cron routines) detect
this line to know the subagent has finished. Without it, orchestrators may time out, respawn
the agent unnecessarily, or report a false failure.

Format:
```
DONE: <output-path> — <N> <items> across <M> <categories>
```

Examples:
```
DONE: stinky-output/ — 12 changes across 3 iterations, LOC -8%
DONE: POTENTIAL_IMPROVEMENTS.md — 7 actionable improvements
DONE: /tmp/alpha-finder.md — 12 picks across 6 themes
DONE: skills/my-skill/SKILL.md — new skill created and tested
DONE: outputs/data.csv — 150 records scraped from 3 sources
```

**Rules for skill authors:**
- Always emit the `DONE:` line as the very last line of your output.
- Include the primary output path so callers know where to find results.
- Add a short human-readable summary after `—` for logs and monitoring.
- Never emit `DONE:` before the work is actually complete.
