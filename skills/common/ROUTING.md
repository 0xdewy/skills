# Meta-skill Routing

Second activation gate for the meta-skills (`goal`, `project-manager`,
`red-team`, `code-smellz`, `pr-smellz`, `shrinkray`), specialized quality
workflows, and domain reference skills.
Frontmatter `TRIGGER`/`SKIP` matches *language*; this table matches task *shape*.
Consult it before running a heavyweight skill: if the matching row names a
different skill, defer to it; if it says **none**, do the work directly and say
so.

## Route by task shape

| The task is… | Route to | Not this |
|---|---|---|
| One scoped action — a single file, command, explanation, or narrow fix | **none — do it directly** | any meta-skill; naming a "do it yourself" skill would trigger on everything |
| A bounded loop toward an executable check, observable criterion, or explicit reviewer gate | **goal** | `project-manager` — use that only for independent workstreams |
| Decompose one mandate into independent slices, dispatch in parallel, integrate | **project-manager** | `goal` — single stream, no decomposition |
| Build genuinely competing candidates, test them, and select one | **project-manager --compete** | `goal` — that follows one implementation stream |
| Find issues in an existing deliverable; produce prioritized findings, don't fix | **red-team** | `project-manager` — that builds/fixes |
| Review behavior introduced by a pull request or merge-base diff, anchored to changed lines | **pr-smellz** | `code-smellz` — that cleans the whole repository; `red-team` — that is not diff-scoped |
| Write or rewrite a pull request's title and description for readers with no context | **pr-describe** | `pr-smellz` — that finds defects, it does not explain the change |
| Infer general behavioral properties and try to falsify them across inputs or state sequences | **invariant-miner** | a direct unit test — that checks one known example; `code-smellz` — that searches broadly for quality problems |
| Reconcile the same behavioral claim across schemas, code, tests, docs, or generated artifacts | **spec-reconciler** | `invariant-miner` — that searches an input/state space; a direct edit — use that when the known correction and authority are already supplied |
| Clean up bugs, security, architecture, or maintainability while preserving behavior | **code-smellz** | `shrinkray` — that optimizes size/dead code |
| Reduce code size, dead files, duplication, or verbosity while preserving behavior | **shrinkray** | `code-smellz` — that optimizes correctness/quality |
| The answer depends on a specific external API, protocol, spec, or dataset | the matching **domain skill** | a generic router — correctness comes from one scoped source, not a catch-all dispatcher |

## Tie-breakers

- **Cheapest route wins.** When two rows match, pick the one that spawns
  fewer agents. A budget is a ceiling, not a target (`scaling.md`).
- **Restraint is the default.** If you are unsure a heavyweight skill is
  warranted, it isn't — take the **none** row, do the direct thing, and state
  that the meta-skill was overkill.
- **One meta-skill owns a run.** They compose by *delegation*
  (`goal → workers`, `project-manager → workers → red-team`), never by triggering
  each other. If you find yourself wanting two coordinators, re-scope.

Skills whose activation is ambiguous should point their in-body activation gate
here rather than re-deriving these boundaries.
