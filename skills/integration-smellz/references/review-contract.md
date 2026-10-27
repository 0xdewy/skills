# Integration review contract

## Lenses

Every reviewer applies all five. Pareto first; severity still wins.

| Lens | Question |
|---|---|
| Pareto | Does the goal need this PR, file, protocol, or coordination at all? Name what to delete or collapse, the cost avoided, and the benefit lost. Look for duplicate sources of truth across PRs, work optimizing something that should be deleted, and fixes riding inside unrelated feature PRs. |
| Correctness | Do invariants, edge cases, error paths, ordering, and retries hold in the composed code, not only the PR's own? |
| Product | Can the user, caller, or operator complete the promised journey, understand failures, upgrade, and recover? |
| Maintainability | Does required code add duplication, wrappers, or coupling that makes a named next change harder? |
| Security | Does the full path keep authorization, approval binding, and validation? Check removed safeguards and newly reachable input. |

Challenge an explicit requirement openly with its lost benefit; never silently
drop it or remove a safeguard. A missing test is a finding only when you name
the plausible regression it would catch.

## Cross-PR checklist

Ordered by how many real defects each check caught in past integrations. The
seam reviewer runs every item that applies; per-PR reviewers run the ones
their seam rows touch.

1. **One name per thing.** Every service that keys on a changed name agrees on
   its form: chain id vs configured name, case, encoding (hex case, checksum),
   route vs package id, path domain. Test two requests that differ in one term.
2. **Follow one value end to end.** Trace a concrete value (amount, address,
   status, limit, advisory) from producer through every hop to what the user
   sees. Units, decimals, rounding, and fields dropped in transit are the usual
   breaks.
3. **Tests exercise what ships.** Each new test must fail with the fix
   reverted. Mocks may return only states the real peer produces. Prefer one
   test across the real service boundary, mount, or release build.
4. **Pins agree.** Every recorded copy of a cross-repo revision matches, is a
   full commit, and is on the upstream default branch or a PR head in the set.
   A dependency pinned in several places must move in all of them.
5. **The composition builds.** Base commits since the PR's merge-base can
   remove or rename symbols the PR uses with no git conflict. Grep the PR's
   added lines for symbols the base changed; build and test the composed tree.
6. **Old readers, new writers.** A strict deserializer (unknown fields denied)
   in a released peer, a rollback binary, or a launcher-written config must
   still accept what the new code writes. Judge against what actually ships.
7. **Every sibling path.** A fix applied to one of several revoke, stage, sign,
   or cleanup paths must reach the others, or the PR must say why not.
8. **Downstream consumers.** Search every consumer repo (plugins, SDK users,
   agents' docs) for a removed or renamed path, field, enum variant, or
   interface version.
9. **Uncertain is not refused.** An unknown, timed-out, or partial outcome must
   not be reported as a clean refusal, retried as new, or have its message
   dropped.
10. **CI ran what it claims.** Filtered tests, skipped platforms, stale shared
    build dirs, and a check named like the release build that is not it.
11. **Protocol line.** Wire version changes match what peers in the shipped
    combination speak; a PR may not require a peer version no landing order
    provides.
12. **Dev and release paths both work.** Behavior behind dev features, debug
    timing, or hardcoded release defaults; state that deployed installs already
    hold.
13. **Description matches diff.** The PR says what it changes, carries no
    unrelated commits, and keeps scope widenings (approvals, permissions) in
    their own PR.

## Recurring single-PR defects

Prime per-PR reviewers with these: tests that pass with the fix removed;
untested main paths; fixtures weaker than the real check; docs promising
behavior the code lacks; cleanup errors failing an operation that already
succeeded; destructive steps before authorization; freshness limits shorter
than a human approval takes; silent truncation; timing bugs that debug builds
hide.

## Severity

- critical: funds move or a signature is produced without the owner's informed
  approval on a path that ships.
- high: a shipped journey fails, or a safeguard can be bypassed by an input a
  shipped producer can send.
- medium: misleading or wrong behavior with a safe failure or workaround, or
  reachable only through an unusual producer or configuration.
- low: docs, cleanup, untested paths, maintainability.

The skeptic pass may lower severity; report its result and the reason.

## Findings

A finding is a defect introduced or worsened by the set, or a concrete cut.
An older bug on a path the PM goal depends on is a finding tagged
`pre-existing`; other older bugs go under Questions.
Pending release work, open PRs, and landing order are not findings. A landing
order that cannot work (cycle, missing prerequisite) is.

`findings.json` is an array:

```json
{
  "id": "I1",
  "lens": "correctness",
  "check": 2,
  "severity": "high",
  "title": "Approval page shows the amount 10^6 too large",
  "prs": ["org/app#12", "org/broker#8"],
  "locations": [
    {"repo": "org/app", "sha": "<full SHA>", "path": "src/plan.rs", "line": 42, "side": "new"},
    {"repo": "org/broker", "sha": "<full SHA>", "path": "src/render.rs", "line": 18, "side": "context"}
  ],
  "evidence": "Producer stores base units in a field the consumer renders as whole tokens.",
  "impact": "The owner approves a payment shown as 1,000,000 USDC.",
  "verification": "Source trace or focused check and its observed result.",
  "skeptic": "survived | lowered | refuted | not run",
  "pre_existing": false,
  "merged_from": ["per-PR reviewer ids this finding absorbs"],
  "recommendation": "Store whole-token amounts, or render base units with decimals."
}
```

`check` is the checklist number, or null. At least one location is a changed
line; unchanged peer code may show the break. Return `[]` when none survive.
Unverified suspicions go under Questions, not Findings.

## Reusing earlier reviews

Earlier review comments are leads, not results. Check whether each is still
present at the current head and composition. A clean individual PR review
does not clear its seams.
