---
name: researcher
description: >-
  Runs scientific literature reviews with a searched corpus, full text,
  supporting and falsifying evidence, and cited synthesis. Only use when
  explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: 0xdewy
  version: 2.0.0
  category: education
  tags:
    - research
    - science
    - literature-review
    - multi-agent
    - hypothesis
    - scientific-method
    - citations
---

# Researcher

Run a cited scientific literature review and write
`research/<slug>/RESEARCH.md`.

Load `../common/patterns/knowledge.md`, `../common/patterns/execution-contract.md`,
and `../common/patterns/scaling.md`. Use scripts in
`scripts/` for paper search/fetch when available. Load `references/report-template.md`
only when writing the report.

## Modes

- `--quick`: focused literature scan, no subagents, 5-10 key sources.
- `--standard`: broad search, evidence table, limited adversarial hypothesis
  check.
- `--thorough`: full query expansion, OA full text where available, pro/con
  hypothesis testing.

## Workflow

1. Convert the question into search queries, inclusion/exclusion criteria, and
   target evidence types.
2. Search primary scholarly sources first. Prefer papers, reviews, trials,
   datasets, and official reports over blogs/news.
3. Record source metadata, claims, methods, limitations, and citation links.
4. For hypothesis work, separately collect supporting and falsifying evidence.
5. Synthesize consensus, live controversies, evidence quality, and practical
   implications. Clearly label speculation.
6. Write `research/<slug>/RESEARCH.md` with citations and a short residual-risk
   section.

Final line:

```text
DONE: research/<slug>/RESEARCH.md — <N> sources, mode=<mode>
```
