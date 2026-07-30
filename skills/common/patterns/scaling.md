# Effort Scaling & Subagent Restraint

Pattern for multi-agent and heavyweight skills. Spawn only the effort the task
actually needs; prefer direct action for simple sub-tasks.

This is grounded in two Anthropic sources:
- "How we built our multi-agent research system" (2025): **scale effort to query
  complexity**. Token usage explained ~80% of outcome variance, and multi-agent
  runs cost ~15× a single chat. Without an explicit scaling rule, a common
  failure mode is "spawning 50 subagents for simple queries."
- "Prompting best practices" (current, Opus 4.5+): Claude now has "a strong
  predilection for subagents and may spawn them in situations where a simpler,
  direct approach would suffice — for example, spawning subagents for code
  exploration when a direct grep call is faster."

Load this alongside `execution-contract.md` and `parallel-agents-guide.md` for
any skill that can spawn agents or run a heavyweight pipeline.

## The Scaling Gate

At the top of a heavyweight skill — after the Activation Gate, before Phase 0 —
assess the task and pick an **effort tier**. State the chosen tier and the
reason in one line so the run is auditable.

| Tier | Use when | Behavior |
|---|---|---|
| **lite** | One obvious action: single-file edit, tiny codebase, a single well-scoped build slice, a one-paragraph review | Work directly. No subagents, no multi-phase pipeline. Do the thing, verify it, emit `DONE:`. |
| **standard** | A few independent parts, a real review needed, moderate codebase | Spawn a small, bounded crew (1–3 agents). One review pass. Normal convergence cap. |
| **full** | Genuinely large: many independent slices, competing approaches, large repo audit, open-ended research | Full crew, parallel waves, the complete review/iteration loop. |

If you cannot decide between lite and standard, start lite and escalate only if
the work actually demands it. Escalation is cheap; over-spawning is expensive
(~15× tokens) and, on current models, a documented failure mode.

## Subagent Restraint

Even at `standard`/`full`, do not spawn a subagent for work that is faster done
directly. Spawn a subagent only when the sub-task meets at least one of:

- It can run **in parallel** with other independent work.
- It needs an **isolated context** (its own large inputs that would bloat the
  orchestrator).
- It is a genuinely **independent workstream** that doesn't need to share state.

For simple tasks, sequential operations, single-file reads/edits, or anything
where the orchestrator needs the context live across steps — work directly
rather than delegating. A direct `grep` or single-file read is almost always
faster than a subagent.

## Delegate Completeness

When you do spawn a subagent, the delegation is complete only if it carries all
four (per Anthropic's multi-agent research — vague delegation caused agents to
duplicate work or leave gaps):

1. **Objective** — what the subagent must produce.
2. **Output format** — the exact file path and schema/structure.
3. **Tool/source guidance** — which tools to use, where to look, boundaries.
4. **Task boundaries** — what is in scope and, crucially, what is *not*.

## Where to Put the Gate

In a skill body, the gate is a short section near the top, for example:

```
## Effort Scaling
Assess the task and pick a tier:
- lite: <one obvious action> → do it directly, skip the crew.
- standard: <a few independent parts> → spawn N agents, one review pass.
- full: <large/parallel/open-ended> → full crew and loop.
State the tier and reason in one line before proceeding.
```

Then each phase says "at tier `lite`, skip this; at `standard`/`full`, run it."
The skill's `evals.json` should include at least one small-task case that
exercises the lite path, so the gate is actually tested.
