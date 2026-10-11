# Anatomy of a PR Description

The reader has no context: a reviewer from another team today, or someone
running `git blame` in two years. Most will read the title. Some will read the
first paragraph. Few will read further. Spend the effort in that order.

## Opening paragraph

Write this first. Two or three sentences, in words a person who has never
seen the codebase would use: what was wrong or missing, what this PR does
about it, what is different afterward. The why lives here.

- No file, function, or class names. No acronym or codename without a gloss.
- Say what a user, operator, or developer will notice, not what was edited.
- It stands alone. A reader who stops here knows what merged and why.
- Don't open with "This PR". Don't repeat the title.
- When no source records the why, write `Motivation: not recorded`. Never
  invent one.

Test: could someone from another team repeat it in a standup after one read?

## Title

Write it last. It is the opening paragraph compressed to one line.

1. Set aside the existing title and the branch name. They record what the
   author planned; the title states what the diff does.
2. Finish the sentence "After this merges, ..." and turn it into an
   imperative.
3. Draft three. Keep the shortest that is still specific.

A good title:

- names the outcome, not the activity: "fix", "update", "refactor", and
  "improve" say nothing without an object and an effect;
- makes sense in a list of fifty titles to someone outside the team;
- covers one change. If it needs "and", name the change that matters and let
  the body carry the rest;
- has no file names, function names, ticket numbers, or `WIP`;
- fits in about 65 characters;
- follows the repo's prefix convention (`fix:`, `feat(api):`) when recent
  merged titles use one: `git log --format=%s -15 <base>`.

| Weak | Strong |
|---|---|
| Fix bug | Return 413 for uploads over 10 MB instead of hanging |
| Updates to auth | Accept expired refresh tokens for 5 minutes after rotation |
| Refactor ExportJob.run() to stream rows + add tests | Stream CSV exports so large reports no longer run out of memory |
| WIP: cleanup | Remove the legacy CSV exporter and its feature flag |

Keep the existing title only when it passes these tests and yours is no
better.

## Body

Everything after the opening is optional. A small fix is the opening plus one
line on how it was verified. Add a section only when a reviewer would miss it.

```markdown
<Opening paragraph.>

## What changed
- <One bullet per behavior the opening did not already cover>

## Not in this PR
- <What a reader would expect to find here but won't, and where it will happen>

## How to verify
- <Tests added; commands run; manual steps; what was not run>

## Risk and rollout
- <Breaking change, migration, config, flag, rollback>

## Reviewer notes
- <Look first at ...; the rest is a mechanical rename of ...>

Fixes #<n>
```

File names belong only in reviewer notes. A long motivation (constraints,
rejected alternatives) gets a `## Why` after the opening; otherwise the
opening is the why.

## Cut the noise

Read each line and ask: would a reviewer miss it? If not, delete it.

- Nothing said twice: the opening does not restate the title, and bullets do
  not restate the opening.
- No empty, `N/A`, or "Risk: none" sections.
- No file-by-file lists; the diff has one.
- No adjectives doing a fact's work: "robust", "comprehensive", "improved",
  "cleaner". Say what is true now that was not before.
- No hedging and no selling. Hacks and limitations are stated plainly.
- A section with one short line becomes a sentence without a heading.

## Before and after

Weak:

> **Update upload handler**
>
> This PR updates the upload handler and adds some tests. Also fixed a few
> lint errors while I was in there.

Strong:

> **Return 413 for uploads over 10 MB instead of hanging**
>
> Uploading a file larger than 10 MB used to hang until the client gave up,
> tying up a server worker the whole time (#482). The server now checks the
> size up front and rejects the upload immediately with a clear error
> (HTTP 413).
>
> The limit can be set with `MAX_UPLOAD_BYTES`; the default is unchanged.
>
> ## Not in this PR
> Uploads sent without a declared size are still read until they hit the
> limit. Tracked in #490.
>
> ## How to verify
> `pytest tests/test_upload.py` covers the limit, the boundary, and the
> config override. Not run: the nginx-fronted staging path.
>
> ## Reviewer notes
> The logic is in `upload.py`; the other six files are lint fixes.
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

- The title names the outcome, and a stranger understands it in a list.
- The opening stands alone and uses no file names, identifiers, or
  unexplained acronyms.
- Every claim traces to the diff, a commit, an issue, or the template;
  nothing substantive in the diff goes unmentioned.
- Verification says what was not run.
- Nothing is said twice, and no line survives that a reviewer would not miss.
