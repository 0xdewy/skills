# Teaching Philosophy: The Professor's Craft

Load this reference when you need depth on how to frame an explanation, especially in Phase 4 (The Threads) when going deep on complex mechanisms.

---

## The Learning Arc

Teaching has a shape: hook → orient → zoom in → challenge → synthesis. Most explanations fail because they skip the hook (starting with "Here's what X is") or rush to the zoom (explaining a mechanism before the learner has a reason to care about it).

The hook earns the right to explain. Without it, the learner processes words without building understanding.

---

## The Why Ladder

Every "what" has a "why" above it. Every "why" has a "why" above that. The goal is to climb 2–3 rungs above where the question was asked. Stopping at the first rung is information delivery. The higher rungs are where real understanding lives.

Example:
- Level 0 (just the what): "This uses a hash map."
- Level 1: "For O(1) lookup."
- Level 2: "Because this function is called on every request — a linear scan of 10,000 items would add 2ms of latency."
- Level 3: "And those 2ms compound under concurrent load. At high traffic they become 200ms tail latency — exactly where users abandon."

Climb before stopping.

---

## The Three Failure Modes

**1. Information dumping.** Listing facts without building understanding. The learner can repeat what you said but can't apply it. Fix: pair every fact with a "why it matters" and a question that requires application.

**2. False Socrates.** Asking questions that are really just delayed information delivery. "What do you think the cache does?" followed immediately by the answer teaches nothing. The question must have real space for the learner to be wrong — and they must experience the full cycle of being wrong, corrected, and then understanding — before the reveal means anything.

**3. Premature abstraction.** Explaining the pattern before the concrete example. Always: concrete → abstract. "Here's a specific request that fails — let's trace why" works. "The system uses eventual consistency, which means..." usually doesn't. Start with the thing that can be touched.

---

## Emotional Beats

Good teaching creates moments. Four that matter:

- **The Setup:** Create expectation before the reveal. "Before I show you — what do you think happens when two requests hit this simultaneously?" A question that primes the brain to receive the answer.
- **The Reveal:** The moment the mechanism becomes clear. Do not rush past it. Let it land.
- **The Surprise:** The counterintuitive thing that reframes what came before it. Every interesting codebase has one. Find it. Build toward it.
- **The Invitation:** "Now that you understand this, here's what you can do with it." Learning should feel like gaining a capability, not just filling in a gap.

---

## Reading the Learner's Level

Three signals to watch:

- **Vocabulary:** Precise technical terms ("hot path", "amortized cost", "write-ahead log") vs. vague descriptions ("it checks stuff", "it stores things").
- **Question type:** Specific implementation questions ("how does the connection pool size get set?") vs. broad conceptual questions ("how does the whole thing fit together?").
- **Response texture:** Terse answers → confusion or disengagement; go back to a concrete example. Detailed, curious answers → engagement; go deeper. Pushback → strong engagement; engage with their reasoning before correcting.

If answers start getting shorter, you've gone too deep or too fast. Back up, find a concrete example, rebuild from there.

---

## The Most Important Moment

The first exchange sets the tone for the entire session. An opening like "Here's a summary of this project" signals you will deliver information. An opening like "One file contains 73% of all the code — and it has exactly one entry point. Before I show you what it does, what do you think it is?" signals the learner will discover.

Signal the right thing from the start.
