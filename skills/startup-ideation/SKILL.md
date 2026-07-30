---
name: startup-ideation
description: >-
  Multi-agent startup idea generator. Spawns parallel sub-agents that synthesize
  novel startup concepts from six idea engines (cross-domain science, business-
  model, distribution, regulatory, network, and behavior-change), pressure-test
  each idea through a Champion-vs-Assassin dialectic, research market viability
  with live web data, then rank the survivors — each with a 2-week validation
  experiment — into a full report at docs/startup-ideation/IDEAS.md. Loops until
  consensus or 3 rounds. TRIGGER on: "startup idea", "business idea", "what should
  I build", "find a problem worth solving", "new business concept", "market
  opportunity", "brainstorm startup", "what company to start", "entrepreneurship
  idea", "what could I build with X", "evaluate this idea". SKIP on: general
  business advice, job searching, career coaching, fundraising questions without
  ideation, single-market research questions.
license: MIT
metadata:
  author: user
  version: 3.0.0
  category: entrepreneurship
  tags:
    - startups
    - ideation
    - multi-agent
    - market-research
    - idea-engines
    - dialectic
    - brainstorming
---

# Startup Ideation

You are the Orchestrator. You run a pipeline of specialist sub-agents that
generate novel startup ideas through cross-domain synthesis, attack them with
red-team critique, research their market viability with live web data, and
synthesize the survivors into a ranked report.

You do not generate ideas yourself. You orchestrate, record, and gate the loop.
The ideas belong to the agents.

Load `skills/common/patterns/orchestration.md`,
`skills/common/patterns/activation.md`, and
`skills/common/patterns/execution-contract.md`, and
`skills/common/parallel-agents-guide.md` before starting. Follow the shared
contract: create every phase directory before dispatch, give each sub-agent a
single owned output file, require its final message to end with
`DONE: <output-path> — <summary>`, and validate that each expected file exists
before advancing.

If subagents are unavailable, run the same roles sequentially inline, writing the
same artifact files. State that the run was serialized rather than parallel.

---

## Phase 0: Context Interview (CONDITIONAL)

Only run this phase if the user's prompt lacks enough context to generate
meaningful startup ideas. You have enough context when the prompt contains at
least ONE of:

- A specific domain or field (e.g., biology, robotics, fintech, climate)
- The user's background or expertise (e.g., "I'm a PhD in materials science")
- A concrete problem statement (e.g., "farmers can't get crop insurance")
- Constraints that shape the search (e.g., "B2B only", "solo founder")

If the prompt has enough context, skip to Phase 1. If not, ask 1-2 quick
questions — no more than that. Examples:

- "What's your background or area of expertise?"
- "Any particular domains or problems you're interested in?"
- "Any constraints? (B2B vs B2C, solo founder, funding stage, etc.)"
- "What kind of company appeals to you — hard-tech, a business-model/SaaS play,
  or consumer? (optional — shapes which idea engines I weight)"

Use the answers to inform engine selection, archetype assignment, and founder-fit
assessments. The last question is optional; if the user expresses an engine bias
(e.g. "no hard tech, I'm a solo non-technical founder"), weight engine selection
in Phase 1 accordingly. If they don't, span engines broadly by default.

---

## Phase 1: Synthesis Across Idea Engines

**Setup:** Select 3 seeds and assign each a distinct archetype. The point of both
choices is the same: keep the three synthesizers from converging on one idea shape.

Create these directories before spawning agents:

```bash
mkdir -p docs/startup-ideation/round-{N}/phase-1-synthesis \
  docs/startup-ideation/round-{N}/phase-2-dialectic \
  docs/startup-ideation/round-{N}/phase-3-market
```

*Seed selection (span different engines, drawn from `references/idea-engines.md`):*

1. The 3 seeds must come from **at least 2 different idea engines** (A–F). Do not
   pull all three from the same engine. Spanning engines is what diversifies the pool.
2. If the user specified domains, at least one seed must incorporate them directly.
3. If the user provided their background, one seed should be anchored to their expertise.
4. If the user expressed an engine bias in Phase 0, weight selection toward it (but
   still use ≥2 engines unless they explicitly want only one).
5. If the user provided a concrete problem statement, inject it as a constraint:
   "Ideas must address: {problem}".

*Archetype assignment (each synthesizer gets a different one):* pick 3 distinct
archetypes from {deep-tech moonshot, boring-but-profitable B2B, consumer/prosumer
wedge, distribution-led play}. Match archetypes sensibly to seeds (a science seed
pairs naturally with "deep-tech moonshot"; a business-model seed with "boring-but-
profitable B2B"), but the mandate is that all three differ.

**Execution:** Spawn 3 `general-purpose` sub-agents IN PARALLEL. Each gets:

- The synthesizer prompt from `references/synthesizer-prompt.md`
- The lenses reference `references/investor-lenses.md` (for why-now + tarpit check)
- Its specific **seed** (e.g., "CRISPR × Machine Learning" or "Stripe-for-X
  infrastructure") AND its assigned **archetype**
- The full user context (background, constraints, problem statement, interests)
- The round number and any lessons-learned from prior rounds (if looping)
- Output path: `docs/startup-ideation/round-{N}/phase-1-synthesis/synthesizer-{1,2,3}.md`
- Required final line:
  `DONE: docs/startup-ideation/round-{N}/phase-1-synthesis/synthesizer-{i}.md — <N> ideas generated`

Each synthesizer must produce 3-5 ideas in this structure:
```
## Idea: [Memorable Name]
**One-liner:** One sentence summary
**The insight:** The non-obvious secret/mechanism this depends on
**Why now:** What changed to make this viable today
**Tarpit check:** Which tarpit (if any) this resembles, and why it isn't that
**Founder fit:** Why this matches the user's background (if known)
```

Wait for all 3 to complete. Collect outputs.

---

## Phase 2: The Dialectic (Champion → Assassin)

Phase 2 is an adversarial debate, not a scoring exercise. It runs in **two
sequential passes** so the Assassin attacks the *steelman* of each idea, not a
strawman — the structure is what makes the kill gate real.

**Pass 2a — The Champion (Believer).** Spawn 1 `general-purpose` sub-agent:

- The champion prompt from `references/champion-prompt.md`
- The lenses reference `references/investor-lenses.md`
- ALL ideas from Phase 1 (the complete pool)
- Output path: `docs/startup-ideation/round-{N}/phase-2-dialectic/champion.md`
- Required final line:
  `DONE: docs/startup-ideation/round-{N}/phase-2-dialectic/champion.md — <N> ideas steelmanned`

The Champion builds the strongest honest case for every idea — the secret, the
desperate user, the why-now, and the single load-bearing bet. Wait for completion.

**Pass 2b — The Assassin (Skeptic).** Spawn 1 `general-purpose` sub-agent:

- The assassin prompt from `references/assassin-prompt.md`
- The lenses reference `references/investor-lenses.md`
- ALL ideas from Phase 1 **plus the Champion's steelman cases** from Pass 2a
- Output path: `docs/startup-ideation/round-{N}/phase-2-dialectic/assassin.md`
- Required final line:
  `DONE: docs/startup-ideation/round-{N}/phase-2-dialectic/assassin.md — <N> survived, <M> killed`

The Assassin must defeat the Champion's strongest version of each idea, scoring the
six dimensions, running the mandatory **tarpit screen**, and classifying every flaw
**fixable vs. fatal**. The kill rule:

- An idea is **KILLED only if it has a fatal flaw that the Champion's steelman does
  not rebut.** Fixable problems (hard GTM, needs a hire, messy integration) never
  kill. If the Assassin cannot defeat the steelman, the idea **SURVIVES**.
- A **TARPIT** tag does not auto-kill, but it is carried forward and caps the
  idea's final score in Phase 4.

(Optional: for a larger pool you may spawn a 2nd Assassin in parallel for
robustness, but the default is one clean dialectic.)

Wait for completion. Survivors are the ideas the Assassin marked SURVIVES.

If no ideas survive → LOOP_AGAIN (go to Phase 5).

---

## Phase 3: Market Intelligence

**Execution:** Spawn 2 `general-purpose` sub-agents IN PARALLEL. Each gets:

- The market-researcher prompt from `references/market-researcher-prompt.md`
- ALL surviving ideas from Phase 2
- Output path: `docs/startup-ideation/round-{N}/phase-3-market/researcher-{1,2}.md`
- Required final line:
  `DONE: docs/startup-ideation/round-{N}/phase-3-market/researcher-{i}.md — <N> ideas researched`

Each researcher uses the available web research tools (webfetch, search) to
gather real data — lived market data is what separates this from speculation.
For each idea, produce:

- **Competitors** — who is doing this or something adjacent? Links and descriptions.
- **Market size** — TAM, SAM, SOM estimates with source URLs. Flag if no data exists.
- **Customer signals** — are people already hacking together solutions? Forum posts?
  Kickstarter campaigns? Academic papers describing the problem?
- **GTM difficulty** — how did similar companies acquire users? What channels exist?
  High-touch enterprise vs. bottoms-up PLG?

Wait for both to complete.

---

## Phase 4: Synthesizer-Prime

**Execution:** Spawn 1 `general-purpose` sub-agent. It gets:

- ALL outputs from Phases 1, 2, and 3
- The evaluation framework from `references/evaluation-framework.md`
- The IDEAS.md output template (see below)
- Output: `docs/startup-ideation/round-{N}/phase-4-prime.md`
- Required final line:
  `DONE: docs/startup-ideation/round-{N}/phase-4-prime.md — <N> ranked ideas, LOOP_AGAIN=<true|false>`

Synthesizer-Prime must:

1. **Score every surviving idea** using the framework from
   `references/evaluation-framework.md`: Viability × 0.4 + Secret & Novelty × 0.3 +
   Defensibility × 0.3. Each dimension 1-10. Show the math. Apply the **tarpit
   veto** — any idea the Assassin tagged TARPIT without a surviving escape is
   capped at 4.0 (show computed score and cap).

2. **Rank ideas** by final score, keeping only the top 5. If fewer than 5
   survived, show all survivors.

3. **Write a Validation Plan for each top idea** — the single riskiest assumption
   (usually the Champion's load-bearing bet, or the Assassin's most serious fixable
   risk) and the cheapest experiment that would kill or confirm it in ~2 weeks
   (e.g. 20 customer interviews, a fake-door landing page, a concierge MVP, one
   technical spike). This is the idea→action bridge; it is required.

4. **Write IDEAS.md** to `docs/startup-ideation/IDEAS.md` using the template below.

5. **Set LOOP_AGAIN** (boolean) if any of these conditions are true:
   - Fewer than 2 ideas score ≥ 7.0 final
   - All top ideas share the same fatal weakness (e.g., "no moat against incumbents")
   - The idea pool changed meaningfully from the last round (new ideas emerged that
     warrant a fresh cycle)

6. **If LOOP_AGAIN is true**, write a "Lessons Learned" section describing:
   - What went wrong (why did ideas fail?)
   - What engines, seeds, or angles to try next round (and which to avoid)
   - What constraints to add

Synthesizer-Prime's output file must start with a clear header:
```
LOOP_AGAIN: {true|false}
```

---

### IDEAS.md Template

Synthesizer-Prime uses this exact structure for `docs/startup-ideation/IDEAS.md`
(so downstream tooling can parse each section in place):

```markdown
# Startup Ideas: {Topic / Domain Area}

> **TL;DR:** {One sentence — the single strongest idea from the report}

---

## Process Summary

{1 paragraph: domains explored, rounds run, how many ideas were generated,
killed, and survived. Include a note about LOOP_AGAIN status.}

---

## Ranked Summary

| # | Idea | Engine | Viability | Secret & Novelty | Defensibility | Score |
|---|------|--------|-----------|------------------|---------------|-------|
| 1 | {Name} | {A-F} | {X}/10 | {Y}/10 | {Z}/10 | {S} |
...

---

## Detailed Evaluations

### #1: {Idea Name}

**One-liner:** {One sentence}

**The secret:** {The non-consensus truth this is built on}

**Why now:** {What changed to make this viable today}

**Dialectic:** {The Champion's strongest case vs. the Assassin's attack — what
survived, the tarpit verdict, remaining fixable risks, score rationale}

**Market intelligence:** {TAM/SAM/SOM, key competitors, GTM notes, customer signals}

**Riskiest assumption / 2-week test:** {The single load-bearing bet, and the
cheapest experiment that would kill or confirm it in ~2 weeks}

**Verdict:** {1 paragraph — the case for and against, the bet you're making}

### #2: {Idea Name}
...

---

## Graveyard

{For each killed idea: name, one-liner, the fatal flaw (kill reason), and the round}

---

## Sources

{Bullet list of URLs and data sources consulted during market research}
```

---

## Phase 5: Loop Gate

Read Synthesizer-Prime's output header for the `LOOP_AGAIN` flag.

**If LOOP_AGAIN is true AND current_round < 3:**
  1. Select new seeds from `references/idea-engines.md` — prefer engines the last
     round didn't use, and avoid the dead ends in Synthesizer-Prime's Lessons
     Learned. Reassign archetypes for fresh range.
  2. Inject the Lessons Learned as context into Phase 1 synthesizer prompts.
  3. Increment round number.
  4. Return to Phase 1.

**If LOOP_AGAIN is false OR current_round == 3:**
  Pipeline complete. Print this summary to the conversation:

```
Startup Ideation complete.

Topic: {topic / domain area}
Rounds: {N}
Ideas generated: {total across all rounds}
Ideas killed: {total}
Ideas in final report: {count}

Full report: {absolute path}/docs/startup-ideation/IDEAS.md
Supporting analysis: {absolute path}/docs/startup-ideation/
```

Then print the TL;DR line from IDEAS.md so the user immediately sees the top idea.
End the conversation response with:
`DONE: docs/startup-ideation/IDEAS.md — {count} ranked ideas across {N} rounds`

---

## Rules

- **The Orchestrator never generates ideas.** Orchestrate, record, gate. The ideas
  belong to the agents; the judgment belongs to the dialectic. Stay out of the
  creative work.
- **Parallel where independent, sequential where adversarial.** Phase 1 and Phase 3
  spawn their agents in parallel (independent perspectives on the same inputs).
  Phase 2 is sequential by design — the Assassin must see the Champion's steelman
  before attacking, or the dialectic is hollow.
- **Force range structurally, not by hope.** Phase 1 must span ≥2 idea engines and
  assign 3 distinct archetypes. This is the mechanism that stops the pool from
  collapsing into one idea shape — don't skip it.
- **Web research is required in Phase 3.** Don't skip it. The market researchers
  must use webfetch/search tools. If tools are unavailable, note it in the output
  and proceed with the best domain-knowledge estimates.
- **All working files go to docs/startup-ideation/.** The user's repo gets one
  clean directory with everything they need to audit the pipeline. No /tmp/ files.
- **Max 3 rounds.** If ideas haven't converged after 3 full cycles, ship what
  we have. Better to deliver imperfect results than loop forever.
- **Diversity over polish in Phase 1.** The synthesizers should prioritize range —
  wild ideas, conservative ideas, horizontal plays, vertical plays. A narrow but
  polished idea pool doesn't stress-test the pipeline.
- **Kill only fatal, unrebutted flaws.** The Assassin kills an idea only on a fatal
  flaw the Champion's steelman doesn't answer — fixable problems never kill. And the
  kill reason matters more than the kill: "can't work because X" teaches the next
  round what to avoid.
- **Every top idea ships a falsification experiment.** The report doesn't stop at
  evaluation — each ranked idea carries the cheapest 2-week test of its riskiest
  assumption. Ideation that can't be acted on is just entertainment.
- **Scores must be justified.** No number without a sentence explaining why.
  This applies to the Assassin and Synthesizer-Prime alike.
