# Evaluation Framework

Use this rubric to score each surviving startup idea. Score honestly — an
inflated score helps no one. The purpose is to separate ideas worth pursuing
from ideas that are merely interesting.

## Scoring Dimensions

### Viability (weight: 40%)
*Can this be built and sold?*

Consider:
- Technical feasibility (from red-team analysis)
- Business model clarity (who pays, how much, through what channel)
- Go-to-market feasibility (from market research)
- Team requirements (can the founder build this?)

| Score | Meaning |
|-------|---------|
| 9-10 | All pieces exist. Clear GTM path. Buildable by a small team within 18 months. |
| 7-8  | Most pieces exist. Some GTM uncertainty but plausible. Buildable with a few hires. |
| 5-6  | Significant technical or GTM risk. Requires a key hire or partnership. |
| 3-4  | Major feasibility gaps. Would require fundamental research or regulatory miracle. |
| 1-2  | Science fiction at current state of technology. |

### Secret & Novelty (weight: 30%)
*Is this built on a non-consensus truth, or just a new feature?*

This dimension folds in the **Thiel lens** (see `references/investor-lenses.md`):
newness alone is cheap; a high score requires a genuine **secret** — a valuable
truth the consensus has missed — not merely a novel juxtaposition.

Consider:
- The secret (is there a real non-consensus insight, or does everyone already agree?)
- Genuine synthesis vs. mere juxtaposition (does the insight only exist here?)
- Competitive landscape (are there 50 startups already doing this?)
- "Wrapper" risk (is this just an API call to an existing service?)

| Score | Meaning |
|-------|---------|
| 9-10 | A real secret. Built on a non-consensus truth that would surprise experts. |
| 7-8  | A non-obvious angle. Most wouldn't see it, but the insight isn't fully contrarian. |
| 5-6  | New-ish, but the consensus already agrees it's a good idea. Incremental. |
| 3-4  | No secret. Multiple funded startups already executing this. Late to the party. |
| 1-2  | Obvious. If it were good, someone would have built it already. |

### Defensibility (weight: 30%)
*Can this be protected from competition?*

Consider:
- Network effects (does value increase with users?)
- Data moat (does usage generate proprietary data that improves the product?)
- Switching costs (how painful is it for customers to leave?)
- Regulatory barriers (does this require licenses/approvals that create a moat?)
- Speed of execution (can a well-funded competitor replicate in 6 months?)
- Technical complexity (is the core tech hard to reproduce?)

| Score | Meaning |
|-------|---------|
| 9-10 | Multiple reinforcing moats. Hard to replicate even with unlimited capital. |
| 7-8  | At least one strong moat. Competitors would need 2+ years to catch up. |
| 5-6  | Some defensibility but thin. Relies primarily on execution speed. |
| 3-4  | Easily replicable. No structural advantage. Features, not a company. |
| 1-2  | Commodity. Anyone with a laptop could compete. |

## Final Score

```
Final Score = (Viability × 0.4) + (Secret & Novelty × 0.3) + (Defensibility × 0.3)
```

Round to one decimal place.

## Tarpit Veto

If the Assassin (Phase 2) tagged an idea **TARPIT** and its escape story did not
hold, **cap the final score at 4.0**, regardless of the computed value. Show both
numbers and the reason, e.g.:

```
Computed: 6.8 → **Capped at 4.0 (TARPIT: marketplace with no defensible take-rate;
no convincing escape).**
```

A tarpit that *did* escape (Assassin tagged CLEAR, or TARPIT with a convincing
escape the Assassin accepted) is not capped — note the escape and score normally.

## Output

For each idea, show the scoring breakdown:

```
### [Idea Name]
- Viability: X/10 — {1 sentence why}
- Secret & Novelty: X/10 — {1 sentence why}
- Defensibility: X/10 — {1 sentence why}
- Tarpit: {CLEAR / TARPIT — escaped / TARPIT — capped}
- **Final Score: X.X/10** {note the cap if applied}
```

Then rank all ideas by final score. The ranking is what goes into IDEAS.md.
