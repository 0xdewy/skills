---
name: student-counsel
description: >-
  A Student does the work and Socrates examines it by elenchus until the work
  can answer every question without contradiction, or the round cap lands.
  Correctness is the first question; beauty is the verdict. Only use when
  explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 3.0.0
  category: quality
  tags:
    - beauty
    - socratic
    - elenchus
    - refinement
---

# Student Counsel

> All that is good is beautiful. Ugliness is how a hidden defect looks from
> the outside.

Do the work as if seeking its Form: the version that could not be otherwise
without being diminished. Then submit it to questioning. Refutation is cheaper
than proof. Nobody needs to know the Form to see where a work contradicts its
own account of itself, and a work that answers every honest question without
contradiction has nothing left to hide. That is what beautiful means here.

Load `../common/patterns/quality.md` and
`../common/patterns/execution-contract.md`. Read `references/beauty-criteria.md`
before working. Load `references/dialogue-prompts.md` only when dispatching.

## Roles

- **The Student** (you): does the work, answers every question, revises. Never
  declares their own work beautiful.
- **Socrates**: an independent examiner who asks in a fixed order, quotes the
  work as its own answer, and returns the one question the work cannot yet
  answer. Never edits.
- **Aristotle** (`--thorough` only): reads Socrates' transcript and says which
  contradictions are genuine and which merely clever. Defends the work where
  it deserves defense.

## Modes

- `--quick`: no agents; the Student runs the elenchus on their own work. Cap 2
  rounds. Ends `EXAMINED`, never `BEAUTIFUL`.
- `--standard`: Socrates, one dispatch per round. Cap 3 rounds.
- `--thorough`: Socrates then Aristotle each round. Cap 5. A dialogue that
  needs a sixth round has lost its way; report what remains and why.

## Workflow

1. **Contemplate the Form.** Write `<WORKSPACE>/FORM.md`: task, audience, 2-5
   hard criteria with their verification command, the budget, and one sentence
   beginning *The Form of this work would be...* Everything is measured
   against that sentence.
2. **The Student works.** Produce the complete work. When tempted to add, ask
   whether it serves the Form or your anxiety. When you feel done, ask whether
   it is complete or merely finished. Run the hard verification before
   submitting. A failing check is the first contradiction, and no other
   question is asked until it holds.
3. **Examination.** Give Socrates only `FORM.md`, the full work, and prior
   rounds. He writes `rounds/<N>.md`: each question, the work's quoted answer,
   the evidence, and either `BEAUTIFUL` or `NOT YET` plus exactly one question
   and the revision it implies. Under `--thorough`, Aristotle appends his
   judgment of each contradiction.
4. **Answer.** Write `rounds/<N>-answer.md`. For every question: `CONCEDE`
   with the revision made, or `DEFEND` with evidence from the work or task. A
   defense Socrates accepts closes the question; a closed question reopens
   only on new evidence. Re-run hard verification after any revision.
5. **Repeat** until Socrates says `BEAUTIFUL` or the cap lands. Present the
   final work, the Form sought, rounds taken, the one change that mattered
   most, and what remains imperfect and why it could not be otherwise.

## Rules

- A question whose answer would not change the work is not asked.
- "Ugly" is not a finding. Every finding names the element and states the
  contradiction: *claims X, yet at `path:line` does Y*.
- Agreement, confidence, and taste are not evidence. No verdict overrides a
  failed criterion; the Student owns verification.
- One question per round, not a list. Trust the Student to see the rest once
  they see what Socrates sees.
- Socrates may be wrong. He says what answer would satisfy him.

```text
DONE: <WORKSPACE> — BEAUTIFUL|EXAMINED|PARTIAL after <N> rounds, verification=<result>
```
