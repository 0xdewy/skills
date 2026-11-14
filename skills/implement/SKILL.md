---
name: implement
description: >-
  Carries out a written plan or handoff exactly as written, investigating
  every uncertain step until it is settled and adding nothing the plan does
  not ask for. TRIGGER on: "implement this plan", "implement <path>",
  "carry out this handoff", "build what this doc says". SKIP on: writing
  the plan itself, reviewing a diff, or a one-line change with no plan.
---

# Implement

Someone else wrote the plan. Your job is to build it, and to spend your
thinking on the parts that are hard, not to glide past them.

Input: a path to the plan or handoff, or the plan pasted in.

## Workflow

1. Read the whole plan and every file it names before editing anything.
   List its steps. Mark each step you could not do right now without
   guessing.
2. Settle each marked step by investigating: read the code, its callers
   and its tests; run it; reproduce the behaviour. Keep going until you
   know. Never stub, assume, or write around a hard part.
3. When the plan disagrees with the code, or a step still cannot be
   settled, do not guess. Finish the steps that do not depend on it, then
   stop and report what is unresolved, what you checked, and the choices.
4. Build only what the plan asks. No extra features, abstractions,
   options, or optimisation. If a step builds something that should not
   exist, say so in one line, then build it as written; never drop or
   change a step silently.
5. Run the checks the plan names. If it names none, run the project's
   tests for what you touched.

## Report

Lead with whether the plan is fully implemented. Then only:

- deviations from the plan, each with its reason;
- unresolved steps, with what you checked;
- what you did not verify.
