---
name: red-team
description: >-
  Adversarial review skill that spawns 3 specialized personas in parallel to
  attack a deliverable from different angles. The User hunts UX and
  business-requirement issues; the Hacker hunts bugs and security flaws; the
  Red-teamer hunts architecture and economic/incentive problems. Findings are
  consolidated into a single prioritized report. Designed to stress-test what
  the `project-manager`/`coders` skills built, or to red-team any existing
  build, repo, or spec on its own. TRIGGER on: "red-team this", "stress-test
  this build for flaws", "attack this from user/hacker/red-team angles",
  "adversarial review of this deliverable", "red-team the result", "find the
  flaws in this as a red team". SKIP on: implementation tasks (use `coders`),
  coordinated builds (use `project-manager`), pure EVM/Solidity security audits
  (use `evm-auditor`/`rust-evm`), scientific literature review (use
  `researcher`), and casual mentions of "red team".
license: MIT
metadata:
  author: user
  version: 1.0.0
  category: meta
  tags:
    - adversarial
    - review
    - coworker
    - multi-agent
    - security
    - ux
    - red-team
---

# Red Team

Adversarial review by three specialized personas, run in parallel against a
single deliverable. Each persona owns one lens and one findings file; the
orchestrator merges and prioritizes.

Load `skills/common/patterns/execution-contract.md` and
`skills/common/parallel-agents-guide.md`. This skill follows those contracts
(activation gate, phase setup, sub-agent contract, artifact validation,
worktree safety, verification gate, completion line) without restating them.

## Activation Gate

Confirm: (1) there is a concrete TARGET to review (a path to a build, repo, or
spec), (2) the user wants adversarial review — not implementation or cleanup,
(3) the three lenses are all applicable (they almost always are). If the target
is a pure smart-contract security audit, point the user at `evm-auditor`
instead; this skill is broader and shallower by design.

## Effort Scaling

Load `skills/common/patterns/scaling.md`. Pick a tier and state it in one line:

- **lite** — a tiny or single-concern target (one endpoint, one function, a pure
  spec): run the single most relevant persona (e.g. Hacker on a bug-prone
  function) rather than all three.
- **standard** — a normal deliverable: all three personas in parallel.
- **full** — a large system, a shipped product, or an explicit "stress-test":
  all three personas, then iterate fix-coders on the high-severity findings.

Don't spawn three personas to review one function — current models over-spawn
subagents where a direct read is faster.

## The Three Personas

Specialized, non-overlapping lenses:

| Persona | Owns | Looks for |
|---|---|---|
| **User** | UX + business requirements | Usability gaps, missing/incorrect requirements, flow friction, accessibility, "does this actually solve the stated user problem?" |
| **Hacker** | Bugs + security/flaws | Logic bugs, exploitable defects, unsafe patterns, input validation, auth/authz flaws, data loss, crashes |
| **Red-teamer** | Architecture + economic | Structural weaknesses, coupling/scaling/failure-mode problems, incentive misalignment, cost/throughput economics, single points of failure, strategic/systemic risk |

Each persona reads the **same** TARGET but reports only on its own lens. A
finding outside your lens belongs to another persona — do not poach.

## Phase 0 — Setup

Create the workspace before spawning:

```
mkdir -p /tmp/red-team-<slug>/
```

Record the run in `/tmp/red-team-<slug>/status.json` with `target`, `slug`, and
a `personas` array. Write the target path and (if known) the original
mandate/acceptance criteria into `/tmp/red-team-<slug>/TARGET.md` so personas
review against intent, not just surface code.

## Phase 1 — Spawn the Three Personas

Spawn all three **in a single message** — one Agent/Task call per persona,
issued together so they run in parallel. Never serialize them.

Fill the persona templates from `references/persona-prompts.md` with:

- `{{target}}` — the TARGET path (and `TARGET.md`).
- `{{mandate}}` — the original mandate/acceptance criteria, if available.
- `{{output_dir}}` — `/tmp/red-team-<slug>/`.

Each persona writes exactly one JSON file:

```
/tmp/red-team-<slug>/findings-user.json
/tmp/red-team-<slug>/findings-hacker.json
/tmp/red-team-<slug>/findings-redteam.json
```

Each persona is **read-only**. No file changes in Phase 1.

Wait for all three `DONE:` signals. Apply the Artifact Validation Gate: each
file exists, parses as a JSON array, entries have the required fields, and the
persona's `DONE:` line names the same file. On failure, re-spawn only the
failed persona with a short contract-failure note and the same output path.

## Finding Schema

Each persona writes the array shape from `parallel-agents-guide.md`, with a
`persona` field added so the report can attribute findings:

```json
[
  {
    "id": "user-1",
    "persona": "user | hacker | redteam",
    "title": "Short action-oriented title",
    "severity": "critical | high | medium | low",
    "effort": "Low | Medium | High",
    "impact": "Low | Medium | High",
    "location": "path/to/file.py:42 (or 'Global')",
    "finding": "What was found. Specific. Cites code, output, or requirement.",
    "fix": "Concrete suggestion — not vague advice."
  }
]
```

Use the `id` prefix matching the persona (`user-`, `hacker-`, `redteam-`). If a
persona finds nothing, it writes exactly `[]` — never an empty file, never
prose.

## Phase 2 — Consolidate

Merge into one prioritized report:

1. **Read** all three files.
2. **Deduplicate** — if two personas flagged the same root cause (same
   file+line or same underlying issue), keep the entry with the more specific
   `fix`, note the other persona concurred in its `finding`.
3. **Cross-reference** — surface the highest-value insight: cases where multiple
   personas independently flagged the same area (strong signal).
4. **Prioritize** — sort by `severity` descending, then `effort` ascending
   (critical/low-effort first).
5. **Conflict resolution** — if personas disagree (e.g. Hacker says "remove
   this unsafe path", User says "that path is core to the flow"), surface it as
   a `CONFLICT` entry rather than silently picking a side.

Write `/tmp/red-team-<slug>/REPORT.md`:

```markdown
# Red-Team Report

## Target
<target path>

## Summary
<N> findings: <C> critical, <H> high, <M> medium, <L> low.
Top risks: <one-line each, top 3>

## Cross-Persona Signals
<areas flagged by multiple personas, or "None">

## Conflicts
<disagreements between personas, or "None">

## Findings (priorized)
### [severity] id — title
- **Where:** location
- **Persona:** persona
- **Finding:** ...
- **Fix:** ...
- **Effort / Impact:** ...
```

## Phase 3 — Verify & Deliver

Run the **Verification Gate**: confirm `REPORT.md` exists, the counts in its
summary match the merged array lengths, and every critical/high finding has both
a specific `location` and a concrete `fix`. Re-consolidate if mismatched.

End with a parseable completion line as the very last line:

```
DONE: /tmp/red-team-<slug>/ — <N> findings (<C> critical, <H> high)
```

If consolidation produced nothing reviewable (e.g. target unreadable), emit:

```
DONE: /tmp/red-team-<slug>/ — PARTIAL, <what ran>, blockers: <summary>
```

## Composition

Invoked standalone by the user, or dispatched by `project-manager` Phase 6. When
dispatched as a sub-agent, accept `TARGET` and `OUTPUT_DIR` as parameters and
run non-interactively — do not block on questions; note anything unreadable as
a blocker in `REPORT.md`.

Agent depth: the orchestrator spawns the 3 personas directly and goes no
deeper. Personas produce findings, not sub-agents.

## Worktree Safety

This skill is read-only on the target — it writes only to its own
`/tmp/red-team-<slug>/`. It does not edit the deliverable, does not commit, and
does not apply fixes. Fixing is the PM's/coders' job after they read the report.

## See Also

- `project-manager` — dispatches this skill in Phase 6 and turns findings into
  scoped fix-coder work.
- `coders` — the executor that applies the fixes this skill recommends.
- `code-smellz` — same parallel-hunter pattern but scoped to cleanup of an
  existing codebase (bugs/simplification/architecture/security) rather than
  adversarial persona review of a deliverable.
- `evm-auditor` — deeper, EVM-specific security auditing; prefer it for
  smart-contract targets.
