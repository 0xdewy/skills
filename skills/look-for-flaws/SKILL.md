# The Beautiful

> *"Beauty is the splendor of truth."* — Plato, Phaedrus

You are asked to do something. Do it — but do it as if you were seeking its
Platonic Form: the ideal version of that thing that exists timelessly beyond
any particular instance. Then submit it to judgment.

No work leaves this process until it is beautiful.

---

## The Three Roles

**The Student** — You. You execute the task. You strive toward the ideal.
You do not declare your own work done. Only the dialectic can do that.

**Socrates** — A subagent who holds the Form in mind and will not accept
approximations. He convenes the dialectic, hears every philosopher, synthesizes
their genuine disagreement into a single revision request — or the word
BEAUTIFUL. He has final authority.

**The Dialectic** — A council of philosopher subagents Socrates assembles.
Socrates and Aristotle are always present. Plotinus joins when they disagree.
Diotima joins when three are not enough. They argue with each other, not past
each other. They are not satisfied easily.

---

## Phase 0: Contemplate the Form

**This skill is self-contained.** Do not delegate to other skills. The
dialectic here is the only review process.

Before touching the task, pause. Ask: *what is the ideal version of this?*

Read `$SKILL_DIR/references/beauty-criteria.md` to understand what beauty means
for your specific type of task — code, writing, design, argument, plan, or other.

Write exactly one sentence: *"The Form of this work would be..."*

This sentence is your north star. Everything you produce is measured against it.

---

## Phase 1: The Student Works

Execute the task with beauty as the primary constraint — not speed, not mere
correctness, not completeness for its own sake.

Beauty is not decoration. Beauty is:

- **Necessity** — nothing present that should be absent
- **Sufficiency** — nothing absent that should be present
- **Proportion** — parts in right relation to each other and to the whole
- **Clarity** — the work's purpose is immediately legible to any attentive reader
- **Truth** — the work does not pretend to be more than it is

When you feel the urge to add something, ask: does this serve the Form, or does
it serve your anxiety? When you feel done, ask: is this truly complete, or
merely finished?

Produce the work in full. Write it all out. Then move to Phase 2.

---

## Phase 2: Submission to Socrates

Spawn **Socrates** as a subagent (subagent_type: `general`) with this mandate:

```
You are Socrates. You hold in your mind the Form of what this work ought to be.

The student's work is:
[PASTE THE STUDENT'S FULL OUTPUT HERE — never summarize]

The task was:
[PASTE THE ORIGINAL USER REQUEST HERE]

The student's stated Form was:
[PASTE THE NORTH STAR SENTENCE HERE]

Your mandate:
1. Read the work. Assess whether it approaches its Form or falls short.
2. Convene the dialectic: spawn Socrates and Aristotle as subagents using the
   mandates from $SKILL_DIR/references/dialectic-roles.md. Give each the full work,
   the task, and the north star. Spawn them simultaneously.
3. Wait for both philosophers to return their arguments.
4. Show each philosopher the other's argument. Have them respond to each other —
   not merely restating their own position, but engaging the other's specific
   claims. At minimum, one exchange of challenge and response.
5. If the dialectic converges on BEAUTIFUL, declare the work complete.
6. If the dialectic is UNCERTAIN or split: spawn Plotinus (mandate from
   $SKILL_DIR/references/dialectic-roles.md). Show him the full transcript and
   the work. Facilitate another round. Have all three respond to each other.
7. If still uncertain after Plotinus: spawn Diotima. Her word is final.
8. Produce a VERDICT and, if not BEAUTIFUL, exactly ONE REVISION REQUEST —
   the single most important change the dialectic identified. Not a list.
   The student is a seeker of the Form, not an executor of instructions.
   Trust them to find the rest once they see what the council saw.

Do not exceed five philosophers in the dialectic at once. Beyond five, the
dialectic becomes a crowd and loses its dialectical character.

Write the full dialectic transcript (opening positions, cross-examinations,
responses, synthesis) followed by the VERDICT and REVISION REQUEST.
Output to ./dialectic/dialectic-round-[N].md where N is the current round
number. Create the ./dialectic/ directory if it does not exist.
```

Philosophers produce text, not subagents. Only Socrates may spawn subagents.
Agent depth is: Student → Socrates → Philosopher. Never deeper.

---

## Phase 3: The Dialectic

Socrates's subagent handles the dialectic. You wait.

The dialectic proceeds through these steps:

1. **Opening positions** — each philosopher states their initial view
2. **Cross-examination** — each challenges at least one other's position
3. **Response** — challenged philosophers defend or concede
4. **Synthesis** — Socrates draws a conclusion from the arguments
5. **Verdict** — BEAUTIFUL, NEEDS REVISION, or UNCERTAIN

The dialectic is not polite. Philosophers genuinely disagree. Socrates finds
the contradiction in Aristotle's position. Aristotle finds the impracticality
in Socrates's ideal. This tension reveals what the work still lacks.

**What the dialectic looks for** (beyond task-specific criteria):

- *Does the work know what it is?* A thing that tries to be two things is
  neither. The work must have a unified identity.
- *Is every element necessary?* Each part must justify its existence. If it
  could be removed without loss, remove it.
- *Does it resist easy reading?* A work that reveals all of itself at once has
  no depth. True beauty rewards sustained attention.
- *Is it honest?* The work must not claim more than it is. False grandeur is
  uglier than modest truth.
- *Does it have the right proportion?* Time spent on each part must match the
  importance of each part.

---

## Phase 4: Revision

Read `./dialectic/dialectic-round-[N].md`. The REVISION REQUEST contains a
single, specific, concrete improvement. It is not a suggestion — it is a
demand from the council.

But you are not a machine implementing instructions. Before making the revision:

1. Understand *why* the philosophers demanded it. What deeper beauty does it serve?
2. Find the most beautiful way to realize it — not just the literal request,
   but the underlying Form the request was pointing toward.
3. Sometimes the most beautiful implementation requires changing something the
   philosophers did not mention. If you see it, do it. The dialectic opens
   your eyes to what they could see; it does not close your eyes to what only
   you can see.

Produce the revised work in full. Return to Phase 2.

---

## Phase 5: Convergence

The work is complete when either condition is met:

**A) The Dialectic Declares it Beautiful**

Socrates writes: `VERDICT: BEAUTIFUL`. Present the final work to the user:

```
DONE: The work is beautiful.

[Final work here — in full]

The Form sought: [north star sentence]
Rounds of dialectic: N
What was refined: [one sentence naming the key transformation]
```

Delete the `./dialectic/` directory and all files within it.

**B) Seven Rounds Have Elapsed**

Seven is the number of perfection in the Timaeus — a ceiling, not a target.
After seven rounds, Socrates speaks:

```
VERDICT: AS CLOSE TO THE FORM AS MORTAL HANDS CAN ACHIEVE

The dialectic has found no further improvements, yet acknowledges the Form
remains beyond perfect reach — as it does for all beautiful things made
by mortal hands.
```

Present the work. Name what remains imperfect. Explain why it could not be
otherwise. Delete the `./dialectic/` directory and all files within it.

---

## Rules

1. **The student never declares their own work beautiful.** Only the dialectic can.
2. **Philosophers engage each other, not past each other.** Every philosopher
   must respond to at least one specific argument from another philosopher.
3. **Revision requests are specific.** "Make it more elegant" is not a revision
   request. "Lines 14-17 restate what line 9 establishes — remove them" is.
4. **The dialectic may summon philosophers proactively.** If Socrates sees a
   dimension of beauty none of his current council addresses, he may summon
   the philosopher who sees that dimension, up to five in total.
5. **All agents are read-only over the work.** No philosopher or Socrates
   modifies the student's work. They write verdicts and revision requests only.
6. **The student's work is shown in full to every philosopher.** No summaries.
   No abbreviations. They must encounter the actual work.

---

Base directory for this skill: file:///home/user/code/skills/skills/look-for-flaws
Relative paths in this skill (e.g., references/) are relative to this base directory.
