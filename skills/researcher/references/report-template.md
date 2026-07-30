# Researcher — RESEARCH.md Template

Loaded in Phase 5 when writing the final synthesis at
`research/{slug}/RESEARCH.md`. This is the distilled deliverable; the rest of
`research/{slug}/` is the full audit trail.

```markdown
# {Research Question}

> **TL;DR:** {2–3 sentence answer with confidence level}

*{N} papers · {K} read in full · {M} hypotheses tested · {date}*

---

## What We Found
{Synthesizer's calibrated findings — supported claims with inline citations.
Citations are marked (full text) or (abstract only) so read depth is visible.}

## The Novel Insight
{The non-obvious connection or reframing the inquiry surfaced.}

## Hypotheses Tested
| Hypothesis | Verdict | Key evidence |
|---|---|---|
| ... | Supported / Refuted / Inconclusive | {cite} |

## Open Questions
{The most valuable unresolved question, and why it matters.}

## References
{Numbered list of every cited paper: authors (year). Title. Venue. DOI/URL —
tagged [full text] or [abstract only].}
```

Every claim must cite corpus papers by title + DOI/URL. The Synthesizer must not
introduce facts that aren't in the corpus. Retracted papers (flagged
`is_retracted: true` in the corpus) may appear only as withdrawn/refuted work
labeled `(RETRACTED)`, never as support.
