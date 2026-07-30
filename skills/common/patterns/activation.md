# Activation Patterns

Loaded by ALL skills. Patterns about when and how skills fire.

Read this at activation. Append discovered patterns at completion.

## Contribution Format

```
### <Pattern Name>
- **Discovered by:** <skill>, <date>
- **Tags:** <tag1>, <tag2>
- **Pattern:** <one sentence>
- **Why:** <one sentence>
```

---

### Dual-Gate Activation
- **Discovered by:** stakeholder-of-last-resort, 2026-05-11
- **Tags:** trigger, skip, false-positive, activation
- **Pattern:** Use two activation gates: TRIGGER/SKIP in frontmatter (gate 1),
  plus a concrete condition check inside the skill body (gate 2).
- **Why:** Frontmatter triggers match on language, not context. A second gate
  evaluates whether the *situation* warrants activation. The skill fires
  linguistically but stays silent contextually when conditions aren't met.

### Heavyweight Workflow Gate
- **Discovered by:** skills review, 2026-06-17
- **Tags:** trigger, multi-agent, false-positive
- **Pattern:** Multi-agent, iterative, or repo-wide skills should trigger on
  explicit workflow intent, not generic verbs like "build", "improve", "docs",
  "memory", or "brainstorm" by themselves.
- **Why:** Heavyweight skills consume time, tokens, and write surface area. The
  activation phrase should prove the user wants that workflow, not merely a
  normal answer or small edit.

### Domain-qualified Generic Terms
- **Discovered by:** skills review, 2026-06-17
- **Tags:** trigger, domain, ambiguity
- **Pattern:** Generic nouns such as "markets", "events", "prices", "auth",
  "memory", "selectors", and "positions" must be qualified by the skill domain
  unless the surrounding user request clearly supplies that domain.
- **Why:** Shared vocabulary across domains causes false positives when the
  metadata relies on bare nouns.
