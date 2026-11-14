---
name: attention
description: >-
  Lists the open pull requests that need the user now: reviews requested
  from them, and their own PRs with conflicts, failing checks, unresolved
  review threads, requested changes, a stale base, or an approval waiting
  to merge. TRIGGER on: "what needs my attention", "what's waiting on me",
  "which of my PRs are blocked". SKIP on: reviewing a PR, fixing a conflict,
  or summarising one repository's history.
---

# Attention

Answer one question: which pull requests need the user right now, and what
does each one need. Read-only.

Run:

```bash
python3 -I scripts/attention.py
```

It reads GitHub through the signed-in `gh` and prints the PRs grouped by
what to do, most blocking first. A PR with nothing to do is left out. Pass
`--input <file>` to read a saved response instead.

## Reply

- Lead with the count that need the user, then the groups in the script's
  order. Skip empty groups.
- Give every PR as its full URL with a few words on what it is.
- Add nothing the script did not report. Do not open, merge, rebase,
  comment on, or fix anything unless asked.
- If `gh` is missing or signed out, say so and stop.
