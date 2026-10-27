---
name: integration-smellz
description: >-
  Deep-reviews every PR in a PM issue or board's multi-repo integration for
  defects, cross-PR contract breaks, and work that can be cut or simplified.
  Read-only. Only use when explicitly requested.
disable-model-invocation: true
---

# Integration Smellz

Find what is wrong with a set of related PRs before they land: defects in each
PR, breaks between PRs and repos, and work to cut. The user knows which PRs
are open. Never report open PRs, landing order, or pending release steps as
results. Read-only: no merges, retargets, pushes, comments, or board edits.
Load `../common/patterns/execution-contract.md` and
`references/review-contract.md`.

## 1. Resolve the set

From a PM issue, board view, or PR URLs, refresh every PR and record repo,
number, base, head SHA, and stack parent. Add merged PRs the open ones build
on and repos that consume what they change (e.g. Petals reading a VFS path).
Do not expand to the whole org. Host scratch policy decides WORKSPACE's
location. Work in full clones under WORKSPACE
(`git clone --shared`, unshallow, fetch `pull/<n>/head`); never fetch into,
check out, or build in a shared checkout. Access failures are coverage gaps.

## 2. Compose against today's bases

Review each PR as it will land, not as it was written.

1. Per repo, merge open PRs in stack order onto the current base tip with
   `git merge-tree --write-tree`. A conflict is a finding. Base commits since
   the merge-base that touch the same files are semantic-merge risks.
2. Check every cross-repo pin each PR records (manifests, lockfiles,
   compatibility files, workflow defaults, test literals): full, on the
   upstream default branch or a PR head in the set, and consistent. A pin to
   a PR head in the set is expected, not a finding.
3. Build the composition in a WORKSPACE clone; run the locked check and the
   PR's tests. A failure is a finding; an unrun build is a gap. Never resolve
   a code conflict: test the head on its own base and mark the composition
   untested. Only the orchestrator builds; finish this step first so
   reviewers start with its results.

## 3. Map the seams

Before review, write `seams.md`: one row per interface a PR changes (wire
types, protocol versions, persisted state, paths, file formats, manifest or
config fields, CLI, policy and idempotency keys, error codes, enums, agent
docs). List its producer and every consumer at the composed revisions,
including released peers that still read it. Each row ends `agrees`,
`breaks: <id>`, or `unchecked: <why>`. The orchestrator owns this file.

## 4. Review

Fresh-context reviewers, at most 6 at once, each writing only its own file
under `reviews/`:

- **Wave 1, one per open PR**: its diff against its stack parent, the PM goal,
  its composition result, and its seam rows. Reads its repo at the head and
  peers at composed revisions. Applies the lenses and recurring patterns;
  returns findings, seam results, and whether it read every changed hunk.
- **Wave 2, one seam reviewer** when more than one repo is involved: takes
  `seams.md`, wave 1 results, and the cross-PR checklist; closes open rows and
  traces each goal producer -> consumer -> user effect, including failure,
  retry, upgrade, and rollback.

Without agents, run the roles in sequence and say so.

## 5. Verify, then report

Re-check every finding against source; keep it only if code shows it or a
focused check reproduces it. Merge shared root causes. For each medium or
higher, run a skeptic pass that tries to refute it, including whether the
behavior is a documented, user-disclosed design. Drop refuted findings and
findings on heads that moved.

Write `INTEGRATION_REVIEW.md`:

1. **Findings** by severity: PR(s), `repo:path:line` at the SHA, what breaks
   for whom, evidence, fix. None? First line says "No defects found".
2. **Cuts**: what to delete or simplify, saved cost, lost benefit. A fix
   riding inside an unrelated PR is a cut.
3. **Coverage**: per PR, SHA, composed or not, finding count, what was not
   read (fully reviewed = every changed hunk read); the seam tally.
4. **Questions**: open points that could hide a defect.

Also write `findings.json`. In chat give the counts and one line per critical,
high, or medium finding and per cut; point to the report for the rest.

Final line:
`DONE: <WORKSPACE>/INTEGRATION_REVIEW.md — <N> findings (<critical>/<high>), <M> cuts, <K>/<T> PRs fully reviewed, <S> seams unchecked`

## Watcher mode

When a host supplies `scope.json` and a stage JSON contract, load
`references/watcher-contract.md`. Its rules replace conflicting ones above.
