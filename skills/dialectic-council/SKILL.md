---
name: dialectic-council
description: >-
  Routes any task through a full multi-model dialectic pipeline: Claude sub-agents
  plus external models (DeepSeek, MiniMax, OpenAI, Gemini) debate the approach,
  implement in parallel, then cross-critique each other's work until reaching
  consensus. API keys stored in ~/.claude/dialectic-keys.json.
  TRIGGER on: "dialectic council", "run through the council", "multi-model debate",
  "get multiple AI perspectives", "have the council implement", "parallel agent
  consensus", "debate and implement", "council of agents", "multi-mind", "polyglot
  debate", "argue about this implementation", "cross-model review", "council debate".
  SKIP on: simple factual questions, tasks where the user wants one fast answer,
  tasks where only Claude is needed, quick lookups, single-line code edits.
license: MIT
metadata:
  author: 0xdewy
  version: 1.0.0
  category: meta
  tags:
    - dialectic
    - multi-agent
    - multi-model
    - debate
    - consensus
---

# Dialectic Council

A multi-model deliberation skill. Any task passes through four phases: **plan**, **execute**, **cross-review**, **synthesize**. A council of AI agents — Claude sub-agents and external model APIs — debate at each phase until they reach consensus.

---

## Phase 0: Setup

Before anything else, check that API keys are configured:

```bash
python3 "$(dirname "$0")/scripts/setup_keys.py" --check
```

If the check fails (no keys file, no external models), run interactive setup:

```bash
python3 "$(dirname "$0")/scripts/setup_keys.py"
```

This creates `~/.claude/dialectic-keys.json` with provider keys. Claude is always in the council. A minimum viable council needs at least one external model alongside Claude. Print the assembled council before proceeding.

For provider details and model IDs, read `references/supported-models.md`.

---

## Phase 1: Planning Debate

Run the planning phase via the orchestrator:

```bash
python3 "$(dirname "$0")/scripts/orchestrate.py" \
  --task "$TASK" \
  --phase plan \
  --session-dir "$SESSION_DIR"
```

**What happens:**

Each council member receives the task and independently produces a structured proposal:

```json
{
  "model": "deepseek",
  "approach": "one-sentence summary",
  "steps": ["step 1", "step 2", "..."],
  "rationale": "why this approach",
  "concerns": ["concern about other approaches"]
}
```

All proposals are collected and shared with every member. Each member then reads the other proposals and produces a disagreements list:

```json
{
  "model": "deepseek",
  "round": 1,
  "disagreements": [
    {
      "target": "claude",
      "point": "specific objection",
      "severity": "blocking|minor"
    }
  ]
}
```

**Convergence rule:** Loop until all `blocking` disagreements are resolved or 5 rounds elapse. Minor disagreements don't block consensus. On convergence, the orchestrator writes `consensus-plan.json` to the session directory.

The planning debate transcript is saved to `$SESSION_DIR/plan-debate.json`.

---

## Phase 2: Parallel Execution

All council members implement the consensus plan independently:

```bash
python3 "$(dirname "$0")/scripts/orchestrate.py" \
  --phase execute \
  --session-dir "$SESSION_DIR"
```

Each model writes its implementation to:
```
$SESSION_DIR/{model_id}/implementation/
```

Claude agents are spawned via `claude --print --dangerously-skip-permissions`. External models receive the full consensus plan as their prompt and return implementation text which is written to files by the orchestrator.

Implementations are collected and logged to `$SESSION_DIR/implementations-manifest.json`.

---

## Phase 3: Cross-Review Debate

Every council member reviews every other member's implementation:

```bash
python3 "$(dirname "$0")/scripts/orchestrate.py" \
  --phase review \
  --session-dir "$SESSION_DIR"
```

**What happens:**

Each reviewer produces a flaw report per implementation:

```json
{
  "reviewer": "minimax",
  "target": "claude",
  "flaws": [
    {
      "id": "flaw-001",
      "location": "function foo(), line 12",
      "description": "off-by-one error in loop boundary",
      "severity": "critical|major|minor",
      "fix": "change i < n to i <= n"
    }
  ]
}
```

All flaw reports are shared with all members. Each member votes on each flaw:

```json
{"flaw_id": "flaw-001", "voter": "deepseek", "verdict": "REAL|NITPICK|INVALID", "reason": "..."}
```

**Voting rules:**
- `REAL` requires majority vote → owner must fix it
- `NITPICK` or `INVALID` by majority → dismissed, does not block consensus
- `critical` flaws require unanimous `REAL` before blocking (prevents gaming)
- `minor` flaws never block consensus even if REAL

Loop until no `REAL` flaws remain or 5 rounds elapse. The full flaw log is saved to `$SESSION_DIR/flaw-log.json`.

---

## Phase 4: Synthesis

Claude acts as the final synthesizer:

```bash
python3 "$(dirname "$0")/scripts/orchestrate.py" \
  --phase synthesize \
  --session-dir "$SESSION_DIR" \
  --output-dir "$PWD"
```

The synthesizer receives:
- All implementations
- The accepted-flaws log (only REAL flaws)
- The consensus plan

It picks the strongest base implementation, applies all validated fixes, and writes the final output to the working directory.

The synthesizer reports which implementation was chosen as the base and which patches were applied.

---

## Running the Full Pipeline

The orchestrator supports a `--phase all` shortcut that runs all phases in sequence:

```bash
python3 "$(dirname "$0")/scripts/orchestrate.py" \
  --task "TASK_DESCRIPTION" \
  --phase all \
  --output-dir "$PWD"
```

When invoked, use `--task` to pass the user's full request verbatim. If the user specifies particular models, pass `--models claude,deepseek,minimax`.

Session state lives in `/tmp/dialectic-council-{uuid}/`. It persists until cleanup so interrupted runs can resume.

---

## Key Paths

| Path | Purpose |
|---|---|
| `~/.claude/dialectic-keys.json` | API keys (never commit this) |
| `/tmp/dialectic-council-{uuid}/` | Session working directory |
| `$SESSION_DIR/consensus-plan.json` | Agreed implementation plan |
| `$SESSION_DIR/implementations-manifest.json` | Where each model's output lives |
| `$SESSION_DIR/flaw-log.json` | All flaws, votes, and verdicts |
| `$SESSION_DIR/plan-debate.json` | Full planning debate transcript |

---

## Completion Signal

End every run with:

```
DONE: dialectic-council — consensus reached in {N} plan rounds, {M} review rounds. Output: {path}
```

If consensus was not reached (max rounds hit), report:

```
PARTIAL: dialectic-council — max rounds hit. {K} unresolved flaws. Output: best available at {path}
```
