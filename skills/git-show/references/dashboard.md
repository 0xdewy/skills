# Dashboard artifact

The default `scripts/collect.py` command produces both JSON and HTML. No manual
translation is needed. For supplied data or targeted enrichment, populate JSON and run:

```bash
python3 <skill-dir>/scripts/render.py snapshot.json dashboard.html
```

Open `assets/dashboard.html` directly for the built-in synthetic preview. The
renderer replaces that demo completely. Keep output outside the skill source.

Snapshot shape (null/missing values mean unknown, never zero):

```json
{
  "scope": "acme/platform · team repositories",
  "collectedAt": "2026-09-09T18:00:00Z",
  "coverage": "12/12 repositories; PR and thread pagination complete",
  "gaps": ["Rulesets inaccessible; readiness unverified"],
  "repos": [{
    "name": "acme/widgets",
    "summary": "3 open PRs · 1 local worktree",
    "local": ["feature/a · staged 1 · unstaged 2 · untracked 0 · upstream unknown"],
    "nodes": [{
      "id": "github.com/acme/widgets:branch:main",
      "kind": "branch", "title": "main", "parent": null
    }, {
      "id": "github.com/acme/widgets#12",
      "kind": "pr", "title": "Repair allocation",
      "number": 12, "parent": "github.com/acme/widgets:branch:main",
      "url": "https://github.com/acme/widgets/pull/12",
      "head": "feature/a", "base": "main", "author": "sam",
      "headRepo": "acme/widgets", "baseRepo": "acme/widgets",
      "branchState": {"headOid": "captured-head-sha", "baseOid": "captured-base-sha",
                      "ahead": 4, "behind": 2, "mergeable": "MERGEABLE",
                      "url": "https://github.com/acme/widgets/compare/base...head"},
      "additions": 95, "deletions": 249, "files": 8,
      "createdAt": "2026-09-01T12:00:00Z", "updatedAt": "2026-09-09T16:00:00Z",
      "signals": [{"label": "CI failed", "tone": "bad"},
                  {"label": "2 unresolved threads", "tone": "warn"}],
      "dependencies": [{"label": "pins broker#60 · SHA verified",
                        "target": "github.com/acme/broker#60",
                        "url": "https://github.com/acme/broker/pull/60"}],
      "details": [{"label": "CI", "text": "Required integration check failed at current head",
                   "url": "https://github.com/acme/widgets/actions/runs/123"}]
    }]
  }]
}
```

IDs are globally unique, parents are within the same repo, and relationships are
acyclic. The renderer rejects malformed topology. Missing parents need explicit
branch nodes. Dependency `target` links to a collected row or falls back to `url`.
Signals use `bad`, `warn`, `good`, or `neutral`; use good only for verified facts.
Filters operate on those tones and labels, not invented aggregate readiness.
Add separate details for checks, approvals, requested reviewers, threads,
conversation activity, head SHA, mergeability, and dependency provenance. The
renderer is presentation only: the collecting agent must supply honest evidence
and coverage, and may extend the template for richer scope-specific needs.

Regression checks live in the repository's `tests/test_git_show.py`. They cover
PR pagination, schema failure stopping the fleet, transient retry limits, the
network budget, partial inventories, fork identity, cycles, legacy CI statuses,
topology rejection, browser filtering and dependency navigation, hostile
content, empty or inaccessible scopes, and narrow layouts. Browser cases need
Chromium and skip without it. They do not validate live org/team discovery or
provider permissions; exercise those against a scoped live target.

## Branch state and dependencies

Branch paths, divergence, suggested next steps, descendants, and declared dependents
are visible without opening details. Branch attention and Dependencies filters retain
tree ancestors; internal links reveal targets even when filtered out. Tree lines
express PR base relationships, not proven commit ancestry or execution order.

`branchState.ahead` and `behind` count commits relative to the captured base SHA,
not the default branch or local upstream. Omit both on unavailable comparisons and
set `error`; unknown must not become zero. `mergeable` uses GitHub's
MERGEABLE/CONFLICTING/UNKNOWN values. Conflicts take precedence over divergence.
Zero behind means only that the captured base is contained, not that all merge
gates passed. Being behind suggests reviewing a rebase or merge; it does not prove
that a rebase is necessary. Parent updates require rechecking descendants, not
blindly rebasing every child. A single snapshot cannot prove historical rebases.

The collector recognizes explicit “Depends on” or “Blocked by” lines with #N,
owner/repo#N, or GitHub PR URLs. It skips fenced examples and HTML comments.
Dependency entries include `evidence` and `evidenceUrl`; arbitrary mentions are not
edges. The collector resolves declared targets to OPEN, MERGED, CLOSED, or UNKNOWN in
`state`, caching duplicate targets without expanding the fleet. Failed lookups
retain `error`. Merged does not prove the consumer integrated that dependency. This bounded extraction cannot
establish dependency completeness, manifest pin freshness, or closed-parent state.

Comparison semantics: [GitHub compare API](https://docs.github.com/en/rest/commits/commits#compare-two-commits).
