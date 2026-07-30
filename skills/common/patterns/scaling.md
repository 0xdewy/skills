# Effort Scaling

Use this contract for any skill that can run a pipeline or spawn subagents.
Default to the cheapest path that can satisfy the request.

## Economy Gate

Before choosing a tier, ask whether no change, deletion, reuse, configuration,
or one direct action satisfies the request. Set task-shaped ceilings for files,
net-new code, dependencies, agents, waves, and iterations; start at zero and
raise only with evidence. Reapply this gate after each phase. Stop when remaining
work cannot affect acceptance criteria; treat a no-op as success.

## Tiers

| Tier | Use When | Behavior |
|---|---|---|
| `lite` / `--quick` | One obvious action, one file, one narrow review, or a direct command can solve it | Work directly. No subagents. Verify and finish. |
| `standard` / `--standard` | A few independent parts or one real implementation/review cycle | Spawn only the useful roles, usually 1-3 agents, one review wave. |
| `full` / `--thorough` | Large/open-ended work with independent sub-goals or explicit request for depth | Run the full skill pipeline with the documented cap. |

Resolution order: explicit user flag → parent `MODE` param → obvious trivial
case = `lite` → skill's non-interactive default. Prompt only when the human is
interactive, no flag/param exists, and mode materially changes cost.

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
justifies its coordination cost.

## Delegation Contract

Every spawned role gets: objective, owned output path, exact output format,
input paths, tool/source guidance, and boundaries. Missing any of these means
the task is not ready to delegate.

Skills that support modes should include at least one `--quick` eval proving the
crew is skipped for trivial work.
