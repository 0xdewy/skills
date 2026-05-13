# Episodic Memory Pattern

Skills accumulate runtime observations in a size-capped rolling window so they
improve across executions without unbounded context growth.

## Architecture

```
learnings/
  episodic.md       ← rolling window: ≤10 lines, loaded on every activation
  archive.md        ← raw observations, only loaded during explicit self-review
```

## Initialization

At skill activation, read `$SKILL_DIR/learnings/episodic.md` if it exists.
Incorporate its compacted insights into your approach. Do NOT read
`archive.md` at routine activation — only during self-review.

## Capture Format

After execution completes (after the `DONE:` signal), append one observation:

```markdown
- [2026-05-11] Trigger: "<trigger phrase>" — <one sentence observation>
```

One line. No more. Be specific:

```
Good:
- [2026-05-11] Trigger: "audit my app's design" — Playwright took 45s on 1280px viewport; 768px and 375px were fast.

Bad:
- [2026-05-11] It went okay.
```

## What to Capture

- **Trigger accuracy** — did the skill fire when it shouldn't have, or fail to fire?
- **Edge cases** — what scenario did the skill not handle gracefully?
- **Performance** — timing, resource usage, sub-agent spawn count
- **Phase transitions** — did any phase fail? Was recovery needed?
- **Pattern discovery** — did the skill discover something other skills should know?
  If so, write to the shared bus at `skills/common/patterns/`.

## Compaction (when episodic.md hits 10 lines)

When `learnings/episodic.md` reaches 10 observation lines:

1. Read all 10 observations
2. Identify the 2-3 most useful insights — those that revealed edge cases,
   changed behavior, or exposed recurring problems
3. Overwrite `learnings/episodic.md` with compacted insights:
   ```markdown
   ## Compacted (last: 2026-05-12, 10 observations)
   - <insight 1>
   - <insight 2>
   - <insight 3>
   ```
4. Append the full raw observations to `learnings/archive.md` with a section
   header indicating the compaction date

After compaction, `episodic.md` contains ≤5 lines. Routine activation reads at
most 10 lines from this file. Explicit self-review reads `archive.md` for the
full history.

## Self-Review

When a skill is explicitly asked to review its own performance, or after every
5 compactions, read `learnings/archive.md` to analyze historical patterns.
Identify trends, stale fixes, and opportunities for revision to SKILL.md.

## Preferences

- Prefer recent observations over old ones
- An insight reconfirmed 3+ times across different dates is a candidate for
  SKILL.md revision
- An observation contradicted by 2+ more recent observations is considered stale
- Observations older than 90 days without reconfirmation carry reduced weight
