# Several PRs

Use when the request names more than one PR. Each PR still gets the full
single-PR review in `SKILL.md`; this file adds only what a set needs. Use
`integration-smellz` instead when the PRs must land together and the question
is whether the combination works: it composes and builds them and maps every
interface between them.

## Setup

1. Fetch metadata for every PR first. Record each head SHA and how the PRs
   relate: same repo, stacked, one containing another's commits, or touching
   the same file, interface, or dependency.
2. One WORKSPACE for the run; each PR gets `<WORKSPACE>/<repo>-<number>/` and
   its own `PR_REVIEW.md`, evidence pack, and lens agents. The mode asked for
   applies to every PR.

## Review each PR alone

Review every PR against its own base, in turn, with no
findings carried between them. Keep at most 6 lens agents running at once.

When one PR contains another's change (a stack, a fold-in, a release branch),
review that change once, in the PR that introduced it, at that PR's current
head. In the containing PR, report only what the combination adds, and re-read
any finding at the container's head before repeating it: the fix may already
be inside.

## Cross-PR pass

After the per-PR reviews, check only the pairs that touch the same file,
interface, or dependency:

- Both sides of a changed contract agree: names, fields, status codes, units.
- A required merge or deploy order is stated and, where it can be, enforced.
- The same fix or helper is not written twice, and overlapping edits do not
  conflict or undo each other.

A cross-PR finding anchors to a changed line in one PR and names the other.
Do not build or merge the PRs together; an unchecked pair is a coverage gap.

## Report

Write `<WORKSPACE>/SUMMARY.md`: one line per PR (URL, what it is, head SHA,
finding counts, report path), then cross-PR findings, then coverage gaps. In
chat give one line per PR and one per critical, high, or cross-PR finding.

Final line:

```text
DONE: <WORKSPACE>/SUMMARY.md — <P> PRs, <N> findings (<critical>/<high>), <X> cross-PR, checks=<passed|partial>
```
