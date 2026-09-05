# Knowledge Patterns

Loaded by reference and research skills (teach-me, researcher, web-scraping).
Also load `execution-contract.md` when the skill writes files, runs scripts, or
produces a durable report.

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

### Domain Router
- **Discovered by:** skills review, 2026-07-01
- **Tags:** routing, domain, handoff, scope
- **Pattern:** A domain reference skill loads only the narrow authoritative
  source for its own domain, states the facts or answer, and hands execution
  back to the caller or a direct edit. It does not grow into a general router
  across unrelated domains ("load any API/spec/dataset").
- **Why:** One "load any reference" skill false-triggers everywhere and drifts
  into an overbroad dispatcher. Correctness comes from a *scoped* source selected
  by that domain's own triggers, not from a broad dispatcher. See
  `skills/common/ROUTING.md` for the domain-skill row.

### Compliance Before Collection
- **Discovered by:** web-scraping hardening, 2026-06-17
- **Tags:** scraping, compliance, data
- **Pattern:** Before collecting website data, write a compliance note covering
  target paths, robots/TOS status, rate limits, user agent, and proceed/stop
  decision.
- **Why:** Scraping mistakes are often process failures. A written gate catches
  disallowed or risky collection before code exists.
