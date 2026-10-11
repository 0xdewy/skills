# Effort Scaling

Use this contract for any skill that can run a pipeline or spawn subagents.
Default to the cheapest path that can satisfy the request.

## Economy Gate

Apply `../pareto/SKILL.md` before choosing a tier and again after each phase:
no change, deletion, or one direct action first; budgets start at zero; a
no-op is success.

## Tiers

| Tier | Use When | Behavior |
|---|---|---|
| `--quick` | One obvious action, one file, one narrow review, or a direct command can solve it | Work directly. No subagents. Verify and finish. |
| `--standard` | A few independent parts or one real implementation/review cycle | Spawn only the useful roles, usually 1-3 agents, one review wave. |
| `--thorough` | Large/open-ended work with independent sub-goals or explicit request for depth | Run the full skill pipeline with the documented cap. |

Resolution order: explicit user flag → parent `MODE` param → obvious trivial
case = `--quick` → skill's non-interactive default. Prompt only when the human
is interactive, no flag/param exists, and mode materially changes cost.

Before work, state one line:

```text
mode: <tier> (<reason>); budget: <max agents/waves>
```

## Spawn Gate

Spawn only when at least one is true:

- The role can run in parallel with other independent work.
- The role needs isolated context that would bloat the orchestrator.
- The role owns an independent workstream with a concrete artifact.

Otherwise do it directly. A budget is a ceiling, not a target. If you need more
agents than the budget, explicitly escalate mode or re-plan.

Default to one dispatch wave. Give each role only its task slice and required
evidence, not the full conversation or another role's transcript. Add a role or
wave only when independent work, adversarial isolation, or a failed criterion
justifies its coordination cost. What each spawned role must receive is the
Subagent Contract in `execution-contract.md`.
