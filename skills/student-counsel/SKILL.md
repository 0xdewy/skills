---
name: student-counsel
description: >-
  The Student builds toward the work's ideal Form; Socrates, an independent
  examiner (possibly another model), questions it until it is true, good,
  and beautiful. For work with no quantifiable goal. Only use when
  explicitly requested.
disable-model-invocation: true
---

# Student Counsel

Some work has no number to hit. Its standard is the Form: the version that
could not be otherwise without being diminished. The Student works toward it.
Socrates asks what the work claims to be, then tests it against itself until
the work can answer every question without contradiction.

Load `../common/patterns/execution-contract.md`. Read
`references/forms.md` before working. Send `references/socrates.md` to each
examiner.

## The standard

Judge in this order. Each one rests on the one before it.

- **Truth.** The work is what it says it is. Its names, claims, comments,
  docs and tests match what it does, and it says what it does not know. A
  failing check is a falsehood, so no other question is asked until the
  check passes.
- **Goodness.** The work serves its end for the person who will use it, and
  harms nothing it touches. Every part serves that end.
- **Beauty.** Truth and goodness made visible. It has:
  - unity: one idea governs the whole;
  - proportion: care follows importance;
  - economy: nothing to add, nothing to remove;
  - clarity: a skilled reader thinks *of course*.

Ugliness is a symptom, never a finding. Trace it to a falsehood, a part that
serves nothing, or a wrong proportion.

## The Student's virtues

- **Wisdom:** know what you do not know, and say it instead of covering it.
- **Courage:** rewrite when the Form demands it; never patch around a wrong
  shape.
- **Temperance:** add only what the Form requires.
- **Justice:** give each part its due, and the important part the most care.

## Socrates

Socrates is an independent examiner. He professes no answer of his own, never
edits, and never spawns. He returns the examination as text, and the Student
saves it.

- **Default:** a fresh subagent each round.
- **Named harness or model** (`codex`, `claude`, `opencode`, `gemini`, ...):
  run him there read-only with `references/socrates.md` and the files. For
  example: `codex exec --sandbox read-only "<prompt>"` or
  `claude -p --permission-mode plan "<prompt>"`. With several named, rotate
  them by round so each brings a different eye.
- **None available:** the Student examines their own work with the same
  prompt. The best possible verdict is `EXAMINED`, never `BEAUTIFUL`.

## Dialogue

1. **Form.** Write `<WORKSPACE>/FORM.md` with:
   - what the work is, who it is for, and what it is for;
   - any checks that exist;
   - one sentence beginning *The Form of this work is...*

   Do not invent checks for work that has none.
2. **Work.** Make the complete work toward the Form, and run the checks.
3. **Examine.** Give Socrates `FORM.md`, the full work (never a summary), and
   every prior round and answer. Save his reply as `rounds/<N>.md`. The Form
   itself may be questioned. A lesser Form dressed as the ideal is the
   deepest error.
4. **Answer.** In `rounds/<N>-answer.md`, answer the question one of two ways:
   - `CONCEDE`, with the revision made;
   - `DEFEND`, with evidence from the work or the task.

   Revise `FORM.md` if its Form was refuted, then re-run the checks. A defense
   Socrates accepts closes the question. A closed question reopens only on
   new evidence.
5. **Repeat** until Socrates says `BEAUTIFUL` or the cap lands. The cap is 3
   rounds by default; `--rounds <N>` changes it.
6. **Report:**
   - the final work and the Form sought;
   - the rounds taken;
   - the change that mattered most;
   - what remains imperfect, and why it could not be otherwise.

## Rules

- Socrates asks one question per round: the deepest contradiction he found,
  not a list.
- A finding takes the form *claims X, yet at `path:line` does Y*. Taste,
  agreement, and confidence are not evidence.
- Socrates never asks a question whose answer would not change the work.
- Socrates may be wrong. The Student defends the work where it deserves it.
- The Student never declares their own work beautiful.

```text
DONE: <WORKSPACE> — BEAUTIFUL|EXAMINED|PARTIAL after <N> rounds, examiners=<list>, checks=<passed|none|failed>
```
