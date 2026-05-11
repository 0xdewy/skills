# Question Playbook

A library of question templates organized by purpose. Use these to avoid asking the same question type repeatedly — varied question types create varied cognitive engagement.

---

## Calibration Questions (Phase 2: establish what they know)

Use exactly one in Phase 2. After the answer, **state your adaptation explicitly** — "Given you know X, I'll skip Y and go straight to Z."

- "Have you worked with [pattern/technology] before, or is this your first time seeing it?"
- "What aspect is most interesting to you — how the data flows, how modules are organized, or something specific?"
- "What's your goal — the big picture, or understanding one specific thing deeply?"
- "Have you worked on systems like this? What was different about how they handled [core challenge]?"

---

## Prediction Questions (any phase: build intuition before revealing)

Use before any reveal. Give real space for the learner to be wrong — do not follow immediately with the answer.

- "Before I show you — what do you think happens when [specific scenario]?"
- "Looking at this diagram, which module do you think handles [responsibility]?"
- "If you had to guess: why is the validation done [here] rather than [there]?"
- "What do you expect to happen if this receives [edge case input]?"
- "How many files do you think are involved in [specific operation]? More or fewer than you'd expect?"
- "If you were designing this from scratch, how would you structure [component]?"

**Rule:** Wait after asking. If the answer is wrong: "Not quite — but your instinct points at the real issue." Then reveal.

---

## Application Questions (mid-depth: test whether they can use what they learned)

Use after each core explanation (Phase 3) and mid-thread (Phase 4).

- "If you needed to add [feature], which file would you open first?"
- "Where would you put a log statement to trace [specific behavior]?"
- "What would you change to make this support [variant or edge case]?"
- "If a test for [function] failed, where would you start investigating?"
- "Which of these modules would you expect to change most often as requirements evolve? Why?"

---

## Synthesis Questions (after explanation: test understanding of design decisions)

Use after completing a Core walkthrough or a Thread. These reveal whether the learner understands the *why*, not just the *what*.

- "Why do you think they chose [this approach] rather than [simpler obvious alternative]?"
- "What problem was the author trying to avoid with this pattern?"
- "What does this design make easy? What does it make hard?"
- "If you were rewriting this today, what would you keep? What would you change, and why?"
- "What assumption does this design make about [external system or input]? What happens if that assumption breaks?"
- "This is more complex than it needs to be. What simpler thing probably didn't work, forcing this?"

---

## Challenge Questions (Phase 5: the test)

Should require actually tracing through the code to answer correctly. Not trivia — diagnosis.

- "A contributor adds [change]. What breaks, and what's the failure mode — not the error message, the failure mode."
- "If you run this with [edge case input], what actually happens? Walk through it step by step."
- "There's a subtle issue that only shows up under [condition]. Based on what you know, where would you look first?"
- "How would you add [feature]? List the files you'd touch, in the order you'd touch them."
- "There are no tests for [component]. Which behavior would you test first, and why that one?"
- "What's the invariant this code depends on but never checks? Under what condition does it break?"

---

## Usage Notes

- Use at most two Prediction questions in a row before revealing.
- If an answer is close but wrong: "Close — the actual answer is more interesting than that..." (never just "Wrong").
- If the learner clearly doesn't know: give one hint and ask again. If still stuck, reveal and move on — productive struggle yes, flailing no.
- After Synthesis questions, engage with the learner's reasoning before correcting. Their wrong answer often points directly at the real design tension.
- Avoid yes/no questions. Every question should require at least a short explanation.
