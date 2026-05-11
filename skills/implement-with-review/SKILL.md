---
name: implement-with-review
description: >-
  Runs a recursive Generator/Skeptic loop between two subagents until an answer
  survives adversarial scrutiny. The Generator proposes and refines; the Skeptic
  (given only the answer, never the question) hunts for the single strongest
  flaw. Loop halts when Skeptic outputs "I cannot find a remaining flaw." — that
  answer is the final output. TRIGGER on: "implement-with-review",
  "oracle-skeptic", "oracle skeptic", "stress-test this answer",
  "proposer critic loop", "find flaws until none remain",
  "adversarial refinement", "refine until right", "best possible answer",
  "make this bulletproof", "keep iterating until solid".
  SKIP on: simple factual lookups, direct code edits, formatting tasks, file
  reads, or anything where one-shot answers are clearly sufficient.
license: MIT
metadata:
  author: iamky1e
  version: 1.0.0
  category: meta
  tags:
    - reasoning
    - adversarial
    - refinement
    - multi-agent
    - quality
---

# Oracle-Skeptic Loop

A recursive proposer/critic loop. No answer is accepted until a second agent has
tried its hardest to break it. The loop repeats until the critique fails.

**Why this pattern works:** the Skeptic is isolated from the original question —
it sees only the answer. This prevents anchoring to the question's framing and
forces the answer to stand on its own. Flaws the Generator rationalizes away
become obvious to an agent that has no context to excuse them.

**Output:** the final answer printed in full, with a brief loop summary
(iterations run, final critique that triggered halt).

---

## Phase 0: Accept the problem

Take the problem from the invocation prompt. If none is provided, ask once:
"What problem or question should I run through the Oracle-Skeptic loop?"

Optionally accept a `max_iterations` parameter (default: 6). This caps runaway
loops on genuinely unresolvable problems.

---

## Phase 1: Generator — initial proposal

Spawn a Generator subagent with this prompt:

> You are the Generator. Your job is to produce the best possible answer to the
> problem below. Be thorough. Make claims only when you can support them. Acknowledge
> genuine uncertainty. Avoid unstated assumptions. Output the answer only — no
> preamble, no "here is my answer".
>
> PROBLEM:
> {{problem}}

The Generator returns the answer text. Store it as `current_answer`.
Initialize `flaw_log = []`.

---

## Phase 2: Skeptic — adversarial critique

**Before spawning the Skeptic:** if `iteration_count >= max_iterations`, halt
immediately and proceed to Phase 5 with the iteration-cap warning. Do not waste
a Skeptic call.

Spawn a Skeptic subagent (`subagent_type: general-purpose`) with this prompt:

> You are the Skeptic. You will be shown an answer. You do NOT know the original
> question. Your sole job: find the single strongest flaw, gap, internal
> contradiction, unsupported claim, or dangerous unstated assumption in this answer.
>
> Rules:
> - Output exactly ONE flaw — the most critical one.
> - Use this exact format:
>   FLAW: "[quote the exact phrase or claim that is flawed]"
>   REASON: [one sentence explaining precisely why it is flawed]
> - Do not hedge. Do not suggest improvements. Do not output anything else.
> - If — after genuinely trying — you cannot find a remaining flaw worth raising,
>   output exactly and only: I cannot find a remaining flaw.
>
> ANSWER:
> {{current_answer}}

The Skeptic returns either:
- A structured `FLAW: / REASON:` block (any output not matching the terminal phrase), or
- Exactly: `I cannot find a remaining flaw.`

---

## Phase 3: Loop decision

**If** the Skeptic's output is exactly `I cannot find a remaining flaw.` (case-insensitive, trimmed):
→ Halt. Proceed to Phase 5.

**If** the Skeptic output is malformed (no FLAW/REASON structure and not the terminal phrase):
→ Treat it as a flaw anyway — append the raw Skeptic output to `flaw_log` and continue.

**Otherwise:**
- Append the flaw to `flaw_log`.
- Proceed to Phase 4.

---

## Phase 4: Generator — revision

Spawn a new Generator subagent with this prompt:

> You are the Generator. Produce a revised answer to the problem below.
>
> A critic has identified the following flaws in previous versions (most recent
> last). Address ALL of them — do not re-introduce a flaw that was already
> caught. Do not mention the flaws in your answer; simply write the improved
> answer.
>
> PROBLEM:
> {{problem}}
>
> FLAWS TO FIX (in order found):
> {{flaw_log as a numbered list}}

The Generator returns the revised answer. Replace `current_answer` with it.
Increment `iteration_count`. Return to Phase 2.

---

## Phase 5: Present the final answer

Print:

```
─────────────────────────────────────────────
ORACLE-SKEPTIC RESULT
Iterations: {{iteration_count}}
Halt reason: {{"Skeptic found no remaining flaw" | "Iteration cap reached"}}
─────────────────────────────────────────────

{{current_answer}}

─────────────────────────────────────────────
```

If the cap was reached, append:

> Note: the iteration cap ({{max_iterations}}) was reached. The Skeptic's last
> critique was: "{{flaw_log[-1]}}". Consider increasing max_iterations or
> reviewing this flaw manually.

DONE: oracle-skeptic completed in {{iteration_count}} iteration(s).

---

## Notes on the Skeptic's isolation

The Skeptic deliberately does not receive the original question. This is
intentional: a truly robust answer should be coherent and defensible on its own
terms. Isolation forces the critique to target:

- Unsupported or overclaimed assertions
- Internal contradictions
- Dangerous unstated assumptions
- Logical gaps between premises and conclusion
- Missing caveats on genuinely uncertain claims

If the question's *context* matters for evaluating tone or scope (e.g., "explain
to a 5-year-old"), include that context inside the answer itself so the Skeptic
can see it. For example: "This answer is written for a non-technical audience:
..."

---

## Composition

- Accepts the problem as a parameter in the invocation prompt.
- Ends with a parseable `DONE:` line for orchestrators.
- Override max_iterations by mentioning it in your prompt: "oracle-skeptic, max 10 iterations: ..." or "run oracle-skeptic with up to 3 rounds on: ...".
- Output is printed to conversation; no file output by default.
