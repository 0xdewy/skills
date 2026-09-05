# Anatomy of a PR Description

The reader has no context: a reviewer from another team today, or someone
running `git blame` in two years. They should understand the change without
opening the diff, and nothing they read should be contradicted by the diff.

## The standard

1. **The first sentence stands alone.** Problem, change, effect, in one
   breath. Someone could repeat it in a standup.
2. **Why before what.** The diff shows what changed. Only the description can
   say why: the symptom, the constraint, the request. When the why exists
   nowhere, say it was not recorded rather than inventing one.
3. **Behavior, not files.** Name what a user, operator, or developer will
   notice. File names belong in reviewer notes, not the summary.
4. **Scope edges.** What is deliberately not in this PR, and where it will
   happen. This stops reviewers hunting for things that were never intended.
5. **Verification is honest.** Tests added, commands run, manual steps taken,
   and what was not run.
6. **Risk only when it exists.** Breaking changes, migrations, config or flag
   changes, rollout order, how to roll back. Omit the section otherwise.
7. **Guide the reviewer.** Where the real change lives; which parts are
   mechanical (renames, generated files, formatting) and can be skimmed.
8. **Plain words.** Short sentences. Expand an acronym the first time.
   Internal codenames get a gloss. No prose a newcomer would have to decode.
9. **Proportion.** A one-line fix gets three lines. A migration gets every
   section. Empty sections and `N/A` are a template failure, not thoroughness.
10. **Nothing the diff cannot back.** Every claim is traceable to a hunk, a
    commit message, a linked issue, or the template.

## Title

Imperative, specific, about 70 characters, naming the effect or the component
and its new behavior.

| Weak | Strong |
|---|---|
| Fix bug | Return 413 for uploads over 10 MB instead of hanging |
| Updates to auth | Accept expired refresh tokens for 5 minutes after rotation |
| WIP: cleanup | Remove the legacy CSV exporter and its feature flag |

## Body

Use the sections that apply, in this order, and drop the rest.

```markdown
<One to three sentences: the problem, what this changes, what a reader notices.>

## Why
<Motivation and constraints. Link the issue or thread. "Motivation: not
recorded" if no source has it.>

## What changed
- <Behavioral change, grouped by concern, with who it affects>

## Not in this PR
- <Deliberate deferral and where it will be handled>

## How to verify
- <Tests added or updated; commands run; manual steps; what was not run>

## Risk and rollout
- <Breaking change, migration, config, flag, rollback>

## Reviewer notes
- <Look first at ...; the rest of the diff is a mechanical rename of ...>

Fixes #<n>
```

## Before and after

Weak:

> This PR updates the upload handler and adds some tests. Also fixed a few
> lint errors while I was in there.

Strong:

> Uploads over 10 MB hung the worker until the client gave up (#482). The
> handler now checks `Content-Length` before reading the body and returns
> 413 with a JSON error.
>
> ## What changed
> - Requests above the limit fail fast with 413 instead of tying up a worker.
> - The limit is configurable with `MAX_UPLOAD_BYTES`; the default is unchanged.
>
> ## Not in this PR
> - Chunked uploads with no `Content-Length` still stream to the size check.
>   Tracked in #490.
>
> ## How to verify
> - `pytest tests/test_upload.py` covers the limit, the boundary, and the
>   config override. Not run: the nginx-fronted staging path.
>
> ## Reviewer notes
> - The logic is in `upload.py`; the other six files are lint fixes.
>
> Fixes #482

## Keep from the existing body

- Checklists the repository's template requires.
- Closing keywords (`Fixes`, `Closes`, `Resolves #n`) so issues still close.
- Screenshots, recordings, benchmarks, and links.
- Human notes that are still true. Restructure them; do not erase them.
- A claim the diff contradicts is removed, and the removal is reported.

## Multiple PRs in one request

Describe each on its own. Do not merge stacked PRs into one narrative, but do
say in each which PR it depends on or unblocks.

## Checklist before applying

- Every claim traces to the diff, a commit, an issue, or the template.
- The first sentence alone tells the story.
- Behavior is named; file names appear only in reviewer notes.
- No acronym or codename goes unexplained.
- Verification says what was not run.
- Nothing in the diff is undescribed at the behavior level, and nothing
  described is absent from the diff.
- Length matches the change.
