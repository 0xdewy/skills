# Knowledge Patterns

Loaded by skills in the Knowledge & Reference category: teach-me, rust-evm,
polymarketv2, web-scraping.

Read this at activation. Also load
`skills/common/patterns/execution-contract.md` when the skill writes files,
runs scripts, or produces a durable report. Append discovered patterns at
completion.

## Contribution Format

```
### <Pattern Name>
- **Discovered by:** <skill>, <date>
- **Tags:** <tag1>, <tag2>
- **Pattern:** <one sentence>
- **Why:** <one sentence>
```

---

### Freshness Gate
- **Discovered by:** polymarketv2, rust-evm hardening, 2026-06-17
- **Tags:** freshness, current-info, versioning
- **Pattern:** If an answer depends on current APIs, laws, prices, package
  versions, protocol forks, or tool flags, verify against a current primary
  source before giving production guidance.
- **Why:** Reference skills go stale silently. Current-sensitive advice can be
  confidently wrong even when the local skill text was correct when written.

### Source Hierarchy
- **Discovered by:** researcher, polymarketv2, 2026-06-17
- **Tags:** sources, citations, authority
- **Pattern:** Prefer primary sources: official docs/specs, standards, source
  repos, papers, or direct data. Use secondary sources only for context and label
  them as such.
- **Why:** Knowledge skills should reduce uncertainty, not launder hearsay into
  authoritative-sounding answers.

### Version and Assumption Header
- **Discovered by:** rust-evm hardening, 2026-06-17
- **Tags:** versions, assumptions, reproducibility
- **Pattern:** For technical answers affected by environment, state relevant
  assumptions: package/tool version, protocol fork, platform, date verified, or
  data window.
- **Why:** Users can only reproduce or safely apply guidance when they know the
  context in which it is true.

### Inference Labeling
- **Discovered by:** skills review, 2026-06-17
- **Tags:** reasoning, uncertainty, citations
- **Pattern:** Clearly distinguish sourced facts, direct observations, and
  inferences from those facts. Use phrases like "The source states..." vs.
  "I infer..." when the answer goes beyond the source.
- **Why:** The most dangerous hallucinations are plausible conclusions presented
  as if they were explicitly sourced.

### Stale Reference Handling
- **Discovered by:** polymarketv2, 2026-06-17
- **Tags:** stale-docs, maintenance, provenance
- **Pattern:** Reference files that encode external APIs or specs should carry
  provenance or a last-verified date. If the date is stale for the domain, check
  upstream before relying on it.
- **Why:** A local reference file is a cache, not the source of truth.

### Compliance Before Collection
- **Discovered by:** web-scraping hardening, 2026-06-17
- **Tags:** scraping, compliance, data
- **Pattern:** Before collecting website data, write a compliance note covering
  target paths, robots/TOS status, rate limits, user agent, and proceed/stop
  decision.
- **Why:** Scraping mistakes are often process failures. A written gate catches
  disallowed or risky collection before code exists.
