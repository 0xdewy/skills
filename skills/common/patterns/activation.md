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
