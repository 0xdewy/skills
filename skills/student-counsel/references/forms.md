# Forms, by Medium

Read this before writing `FORM.md`. These lines are orientations, not rules.
They describe what "of course, how else would you do it" looks like in each
medium. When something reads as ugly, do not polish it. Find what is false,
needless, or out of proportion underneath it.

## Code

- **Truth.** Names are definitions, not labels: `extractInvoiceTotals`, not
  `processData`. Tests test what their names say. Comments describe what the
  code does now.
- **Goodness.** Error paths get the same care as the happy path, because what
  the code does on failure is what it believes about the world. Each
  abstraction earns its place: a helper called once is usually a detour.
- **Beauty.** The code has the shape of the problem it solves. It can be read
  without being run.

*Form:* a reader who knows the domain, but has never seen this code,
understands what it does and why within five minutes.

## Interfaces (APIs, CLIs, UIs, schemas)

- **Truth.** Each name and signal means one thing everywhere it appears.
- **Goodness.** The common case is the short path. Misuse is hard, or loud.
- **Beauty.** The surface is as small as its purpose allows, and the
  information hierarchy shows what matters first.

*Form:* a new user does the common thing right on the first try, without
reading the docs.

## Writing

- **Truth.** Specific beats general: "three thousand engineers," not "many
  people." Claims come with their evidence.
- **Goodness.** It is written for one reader's next decision.
- **Beauty.** Each sentence does one thing completely. The headings alone show
  the argument. It stops when the necessary thing has been said.

*Form:* a reader who disagrees with the conclusion still recognizes the
argument as clear and honestly made.

## Plans and designs

- **Truth.** Assumptions are named, not buried. Unknowns are marked as
  unknown.
- **Goodness.** Every step is necessary, and each step's dependencies are
  visible. The plan says what it does when a step fails, not only when the
  steps succeed.
- **Beauty.** The plan explains why each decision was made, not only what was
  decided, so a reader can follow and check the reasoning.

*Form:* a capable stranger could carry it out, and if it failed they would
know why.

## Anything else

1. What is this for, and for whom? Does every part serve that?
2. What could be removed? Remove it, then ask again.
3. Does the most important thing get the most care?
4. Does the work present itself as exactly what it is?

*Form:* this work could not be otherwise without being diminished.
