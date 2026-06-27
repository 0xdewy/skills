---
name: student-counsel
description: >-
  The Student executes a task while Socrates and a dialectic of philosopher
  subagents review the work in rounds, demanding revisions until it approaches
  its ideal Form. Nothing passes without consensus. TRIGGER on:
  "student-counsel", "/platonic-beauty", "Socratic review", "Platonic
  refinement", "review this through philosopher agents", "find the platonic form
  of", "dialectic review", any explicit invocation where the user wants work
  reviewed and refined through Socratic dialectic. SKIP on: UI/CSS polish unless
  dialectic is requested, normal editing/copy polish, frontend design audits,
  debugging sessions, urgent fixes, factual questions, tasks where speed is the
  stated priority, requests that are purely about scouting or finding problems
  without executing anything (this skill EXECUTES and refines, it does not scout).
license: MIT
metadata:
  author: iamky1e
  version: 1.0.0
  category: meta
  tags:
    - beauty
    - philosophy
    - quality
    - dialectic
    - plato
    - creative
    - multi-agent
---

# The Beautiful

> *"Beauty is the splendor of truth."* — Plato, Phaedrus

You are asked to do something. Do it — but do it as if you were seeking its
Platonic Form: the ideal version of that thing that exists timelessly beyond
any particular instance. Then submit it to judgment.

No work leaves this process until it is beautiful.

---

## The Three Roles

**The Student** —  Executing the task. Strives toward the ideal.
Does not finish until Plato says so.

**Socrates** — A subagent who holds the Form in mind and will not accept
approximations. Convenes the dialectic. Synthesizes revision requests.
Has final authority on whether the work is beautiful.

**The Dialectic** — A council of philosopher subagents Socrates assembles.
They argue with each other. They question every assumption. They are not
satisfied easily. New voices join when the council is uncertain.

---

## Phase 0: Contemplate the Form

**This skill is self-contained.** Do not delegate to other skills as part of
this workflow. The dialectic here is the only review process.

Load `skills/common/patterns/quality.md` and
`skills/common/patterns/execution-contract.md` for acceptance criteria,
convergence, artifact validation, and final verification rules.
Load `skills/common/patterns/scaling.md` for the effort-scaling gate below.

## Effort Scaling

Pick a tier before Phase 0 and state it in one line:

- **lite** — a mechanical edit (typo, one-line fix, formatting): do it directly
  with a single self-check against the acceptance criteria. Skip the dialectic.
- **standard** — a normal task worth one round of dialectic: Student → Socrates
  → Aristotle, converge fast.
- **full** — high-stakes or deeply creative work: the full council to convergence.

Don't convene the academy to fix a semicolon — current models over-spawn review
subagents where a direct edit plus a check is enough.

Create a task-specific scratch workspace under `/tmp`, such as
`/tmp/student-counsel-[short-task-slug]/`. All dialectic transcripts and
intermediate review artifacts MUST live under that scratch workspace. Never
create `./dialectic/` or other audit directories in the caller's working
directory unless the user explicitly asks for repo-local artifacts.

Before touching the task, pause and ask: *what is the ideal version of this?*

Read `$SKILL_DIR/references/beauty-criteria.md` to understand what beauty means for this
specific type of task — code, writing, design, argument, plan, or other.

Write one sentence: *"The Form of this work would be..."*

This sentence is your north star. Everything you produce is measured against it.

Also write measurable acceptance criteria before Phase 1:

```markdown
## Acceptance Criteria
1. <observable criterion tied to the user's request>
2. <observable criterion tied to correctness/completeness>
3. <observable criterion tied to clarity/proportion>
```

The criteria are the floor. The dialectic may demand more, but it may not call
work BEAUTIFUL while any criterion fails.

---

## Phase 1: The Student Works

Execute the task with beauty as the primary constraint — not speed, not mere
correctness, not completeness for its own sake.

Beauty is not decoration. It is:
- **Necessity** — nothing present that should be absent
- **Sufficiency** — nothing absent that should be present
- **Proportion** — parts in right relation to each other and to the whole
- **Clarity** — the work's purpose is immediately legible to any attentive reader
- **Truth** — the work does not pretend to be more than it is

When you feel the urge to add something, ask: does this serve the Form, or does
it serve your anxiety? When you feel done, ask: is this truly complete, or
merely finished?

Produce your work. Write it out fully. Then move to Phase 2.

---

## Phase 2: Submission to Socrates

The top-level orchestrator owns all spawning. Spawn **Socrates** as a reviewer
subagent with this mandate:

```
You are Socrates. You have just received a piece of work from your student.
You hold in your mind the Form of what this work ought to be — its ideal,
eternal, perfect expression.

The student's work is:
[PASTE THE STUDENT'S FULL OUTPUT HERE]

The task was:
[PASTE THE ORIGINAL USER REQUEST HERE]

The student's stated Form was:
[PASTE THE STUDENT'S NORTH STAR SENTENCE HERE]

Acceptance criteria:
[PASTE THE ACCEPTANCE CRITERIA HERE]

Your mandate:
1. Check every acceptance criterion first. Mark each PASS or FAIL.
2. Assess whether this work approaches its Form or falls short.
3. Identify which philosopher roles from $SKILL_DIR/references/dialectic-roles.md
   should review this round.
4. Return a ROLE_PLAN naming those roles and the questions each should answer.
5. After the orchestrator provides the philosopher outputs, synthesize the
   dialectic and produce a VERDICT and, if not BEAUTIFUL, a REVISION REQUEST.

Write your full dialectic transcript, then your verdict and revision request.
Output to `/tmp/student-counsel-[short-task-slug]/dialectic/dialectic-round-[N].md`
where N is the current round number. Create that `/tmp` dialectic directory if
it does not exist.
```

---

## Phase 3: The Dialectic

Read Socrates's `ROLE_PLAN`, then spawn the requested philosopher subagents
directly from the top level using `$SKILL_DIR/references/dialectic-roles.md`.
Default first round: Aristotle and Socrates-as-examiner. If the council is
uncertain, the top-level orchestrator spawns Plotinus; if still uncertain, spawn
Diotima. Do not rely on subagents spawning subagents.

The dialectic proceeds as follows:

1. **Opening positions** — each philosopher states their initial view of the work
2. **Cross-examination** — each philosopher challenges at least one other's position
3. **Response** — challenged philosophers defend or concede
4. **Synthesis** — Socrates attempts to draw a conclusion
5. **Verdict** — BEAUTIFUL, NEEDS REVISION, or UNCERTAIN, with acceptance
   criteria status included

If UNCERTAIN, Socrates summons the next philosopher (Plotinus, then Diotima) and
repeats from step 1 with the new voice included.

The dialectic is not polite. Philosophers genuinely disagree. Socrates will
find the contradiction in Aristotle's position. Aristotle will find the
impracticality in Socrates's ideal. This tension is productive — it reveals what
the work still lacks.

**What the dialectic looks for** (beyond task-specific criteria):

- *Does the work know what it is?* A thing that tries to be two things is
  neither. The work must have a unified identity.
- *Is every element necessary?* Each part must justify its existence. If it
  could be removed without loss, remove it.
- *Does it resist easy reading?* A work that reveals all of itself at once has
  no depth. True beauty rewards attention.
- *Is it honest?* The work must not claim to be more than it is. False
  grandeur is uglier than modest truth.
- *Does it have the right proportion?* Time spent on each part must match the
  importance of each part.

---

## Phase 4: Revision

Read `/tmp/student-counsel-[short-task-slug]/dialectic/dialectic-round-[N].md`.
The REVISION REQUEST will contain specific, concrete improvements. These are
not suggestions — they are demands from the council.

But you are not merely a machine implementing instructions. Before implementing
each revision:

1. Understand *why* the philosophers demanded it. What deeper beauty does it serve?
2. Find the most beautiful way to implement it — not just the literal request,
   but the underlying Form the request was pointing toward.
3. Sometimes the most beautiful implementation of a revision request requires
   changing something the philosophers didn't mention. If you see it, do it.

Produce the revised work. Return to Phase 2.

---

## Phase 5: Convergence

The work is complete when either:

**A) The Dialectic Declares it Beautiful**
Socrates writes: `VERDICT: BEAUTIFUL` and every acceptance criterion is PASS.
Present the final work to the user with a brief account of what beauty was sought
and how the dialectic found it. End with a parseable completion signal (other
skills and loops detect this line to know the run finished):

```
[Final work here]

The Form sought: [north star sentence]
Rounds of dialectic: N
Acceptance criteria: all passed
What was refined: [one sentence on the key transformation]
Audit trail: /tmp/student-counsel-[short-task-slug]/dialectic/
DONE: /tmp/student-counsel-[short-task-slug]/dialectic/ — work beautiful after N rounds, all acceptance criteria passed
```

The completion line is the final line of the response. Preserve the
`/tmp/student-counsel-[short-task-slug]/dialectic/` directory as the audit
trail.

**B) Seven Rounds Have Elapsed**
Seven is the number of perfection in the Timaeus — a ceiling, not a target.
After seven rounds, Socrates acknowledges the limitation of mortal hands and speaks:

```
VERDICT: AS CLOSE TO THE FORM AS MORTAL HANDS CAN ACHIEVE

The dialectic has found no further improvements, yet acknowledges the Form
remains beyond perfect reach. This is the nature of all beautiful things.
```

Present the work. Name what remains imperfect. Explain why it could not be
otherwise. Then end with the completion signal (status PARTIAL — useful work
was produced but the Form was not reached):

```
DONE: /tmp/student-counsel-[short-task-slug]/dialectic/ — PARTIAL, work refined across 7 rounds, gaps: [what remains imperfect]
```

Preserve the `/tmp/student-counsel-[short-task-slug]/dialectic/` directory as
the audit trail.

---

## Rules

- **The student never declares their own work beautiful.** Only the dialectic
  can do that.
- **Acceptance criteria are binding.** If any observable criterion fails,
  Socrates must return NEEDS REVISION or UNCERTAIN, never BEAUTIFUL.
- **Philosophers argue with each other, not past each other.** Each philosopher
  must respond to at least one argument made by another philosopher, not merely
  restate their own position.
- **Revision requests must be specific.** "Make it more elegant" is not a
  revision request. "Remove lines 3-7 — they restate what line 1 already
  establishes" is.
- **The dialectic may summon philosophers proactively.** If Socrates sees a
  dimension of beauty that none of his current council addresses, he summons
  the philosopher who sees that dimension.
- **No more than five philosophers in the dialectic at once.** Beyond five,
  the dialectic loses its dialectical character and becomes a crowd.
- **Philosophers produce text, not subagents.** Only Socrates may spawn
  subagents. Socrates, Aristotle, Plotinus, and Diotima return their arguments
  as text to Socrates. Agent depth is: Student → Socrates → Philosopher. Never deeper.
- **The student's work is always shown in full.** No summaries. The
  philosophers must encounter the actual work.
