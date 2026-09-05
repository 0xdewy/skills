# Skills

AI behavior packs that coding agents can load for specialized roles. Skills are
closer to workflows than prompt templates: they define activation boundaries,
tooling, verification, and completion signals.

---

## Install

First, install the `skill` CLI to your system:

```bash
./install.sh
```

This symlinks `skill` into a directory on your PATH so the installed command
stays synchronized with the repository source.

```bash
skill install-all            # install every skill in this repo
skill install <path|url>     # install one skill from a local dir or git URL
skill remove  <name>         # remove one
skill list                   # list installed skills
skill update  <name>         # pull latest for git-cloned skills
skill repair                 # repair links and prune broken managed links
skill -y reinstall-all       # non-interactive full relink for scripts/CI
```

Local skills are linked through a central store into Codex, Claude, OpenCode,
Agents, and Hermes discovery directories. `skills/common/` is linked alongside
them so sibling-relative `../common/...` references work after installation.
`skill repair` removes only broken links that point into that managed store;
unrelated user-managed links are preserved.

See [INSTALL.md](INSTALL.md) for Python and system requirements.

---


Every skill is one of two kinds, read off its frontmatter:

- **Model-invocable.** The description carries concise `TRIGGER` and `SKIP`
  phrase boundaries so the agent can route to it:

  ```yaml
  description: Does X. TRIGGER on: "audit my design", "fix the UI".
               SKIP on: "performance issues", "add a backend endpoint".
  ```

- **Human-only.** Costly workflows and personas set
  `disable-model-invocation: true` and say they run only when explicitly
  requested. No trigger list.

```
You: "audit my app's design"
Agent: [loads frontend-ux-designer skill]
Agent: "Evaluating layout consistency, typography, color, spacing..."
```

---

## The Skills

**Orchestration** — skills that spawn and coordinate multiple sub-agents:

| Skill | What it does |
|---|---|
| [goal](skills/goal/SKILL.md) | Iterates toward fixed criteria, executable checks, or explicit review gates |
| [project-manager](skills/project-manager/SKILL.md) | Runs resumable multi-slice builds, integration, and optional competing candidates |
| [red-team](skills/red-team/SKILL.md) | Adversarial findings report for an existing deliverable |
| [code-smellz](skills/code-smellz/SKILL.md) | Correctness, security, architecture, and maintainability cleanup |
| [pr-smellz](skills/pr-smellz/SKILL.md) | Diff-scoped PR review with changed-line findings and targeted checks |
| [shrinkray](skills/shrinkray/SKILL.md) | Size/dead-code/duplication reduction while preserving behavior |

**Quality** — skills that demand excellence through adversarial refinement:

| Skill | What it does |
|---|---|
| [student-counsel](skills/student-counsel/SKILL.md) | The Student works, Socrates examines by elenchus, revise until the work answers for itself |
| [pareto](skills/pareto/SKILL.md) | Subtraction-first restraint with explicit change budgets |

**Frontend & Testing** — browser-based QA and design auditing:

| Skill | What it does |
|---|---|
| [frontend-twerkin](skills/frontend-twerkin/SKILL.md) | Playwright workflow QA with scoped auto-fixes |
| [frontend-ux-designer](skills/frontend-ux-designer/SKILL.md) | Rendered UI/UX audit and targeted visual fixes |

**Contract Analysis** — discovers behavioral properties and cross-artifact drift:

| Skill | What it does |
|---|---|
| [invariant-miner](skills/invariant-miner/SKILL.md) | Mines implied behavioral properties and tries to falsify them with generative tests |
| [spec-reconciler](skills/spec-reconciler/SKILL.md) | Reconciles source-anchored claims using repository-declared authority |

**Knowledge & Integration** — skills that bring deep domain expertise or
operate a named system:

| Skill | What it does |
|---|---|
| [rust-evm](skills/rust-evm/SKILL.md) | EVM internals: revm, Foundry, bytecode, Yul, gas optimization |
| [hyperliquid](skills/hyperliquid/SKILL.md) | Hyperliquid developer reference: HyperCore/HyperEVM APIs, signing, HIPs |
| [polymarketv2](skills/polymarketv2/SKILL.md) | Polymarket v2 APIs and SDKs: Gamma, Data, CLOB, auth, orders |
| [llm-providers](skills/llm-providers/SKILL.md) | Hosted LLM API endpoints, authentication, SDKs, models, and provider-specific constraints |
| [myco](skills/myco/SKILL.md) | Native Myco identity, groups, messaging, ACL, and Kanban operations |
| [web-scraping](skills/web-scraping/SKILL.md) | Compliant Playwright/httpx scraping, pagination, structured extraction |

**Meta** — skills that create, curate, and constrain other skills:

| Skill | What it does |
|---|---|
| [skill-lab](skills/skill-lab/SKILL.md) | Create, refine, evaluate, and publish skills |
| [agentify](skills/agentify/SKILL.md) | Live read-only repo map for lazy code navigation |
| [vfs-docs](skills/vfs-docs/SKILL.md) | Self-describing docs/ trees: names carry the meaning, depth is zoom, `tree docs/` is the index |

---

## Retired and Replaced Skills

Retired skills remain recoverable from Git history; they are deliberately not
installed or exposed as active routes. Do not restore one merely to preserve a
name—restore it only if its behavior is not covered by the replacement.

| Retired skill | Current route |
|---|---|
| `implementer` | `goal` for one bounded implementation loop |
| `one-shot-project` | `project-manager` for dependency-aware multi-slice builds |
| `coders` | Direct implementation or a `project-manager` worker slice |
| `brainstormers` | `project-manager --compete` when genuine competing candidates are required |
| `startup-ideation` | `project-manager --compete` |
| `ego` | none; a voice belongs in the system prompt, not a skill |
| `teach-me` | a direct explanation; `agentify` for a code map |
| `researcher` | none; search and cite primary sources directly |
| `simple-memory` | Retired from active discovery; persisted memory is user data and must use a purpose-built, consented store |
| `skill-creator` | `skill-lab` for repository-authored skills; the platform system skill remains separate |

`agentify` and `vfs-docs` are both active: `agentify` maps code for lazy
navigation, while `vfs-docs` builds self-describing documentation trees. They
are not aliases and neither should be deleted as part of the split.

## Plugin Compatibility

This repository installs skills, not Codex plugins. A plugin pack that embeds
these skills must keep its own manifest and marketplace validation in its
native toolchain. Validate archived Claude plugin packs with
`claude plugin validate <pack-root>`; validate Codex plugins with the Codex
plugin manifest validator. Do not treat marketplace availability as an
installation—verify installed status separately.

---

## Design Principles

- **Routing before weight.** Frontmatter catches user language; `../common/ROUTING.md`
  catches task shape. If a task is one direct action, do it directly.
- **Cheap first.** Skills with modes start at `--quick` unless the task
  genuinely needs parallelism, isolated context, or multiple workstreams.
- **Lazy context.** Keep `SKILL.md` small. Put long prompts, examples, scripts,
  and domain facts in lazy-loaded resources.
- **Evidence-backed completion.** `DONE:` is earned by checks, artifacts, or
  cited evidence, not by reviewer enthusiasm.

## Validation

Run the lightweight repo validator after skill edits:

```bash
python3 scripts/validate_skills.py
```

It checks skill frontmatter, size limits, stale forbidden strings, meta-skill
routing references, invocation contracts, token budgets, and eval JSON.

To execute evals against a live agent backend and grade the results:

```bash
python3 scripts/run_evals.py --skill goal                 # run one skill's evals
python3 scripts/run_evals.py --skill goal --id 3          # one eval
python3 scripts/run_evals.py --all --dry-run              # plan only (no invocations)
```

The runner auto-detects `claude`/`codex`/`opencode` (prefer claude), captures
artifacts per eval into the results dir, and grades via the skill's own
`evals/grade.py` or the canonical generic grader. Use `--backend`, `--model`,
`--grader`, and `--timeout` to override defaults.

For evals with outcome-only assertions, compare the skill against direct work:

```bash
python3 scripts/run_ablation.py --skill invariant-miner --id 3
```

Pass `--grader-model codex:<model>` to judge with Codex instead of the default
Anthropic/Claude path.

Check volatile domain references without network access:

```bash
python3 scripts/check_domain_freshness.py
```

---

## Creating a Skill

Skills are `SKILL.md` files with YAML frontmatter that declare their name and
description:

```markdown
---
name: my-skill
description: What it does. TRIGGER on: "these phrases". SKIP on: "those phrases".
---

## Workflow
1. Understand the problem.
2. Do the work.
3. Verify.

DONE: <output> — <summary>
```

To create one properly, use the skill that knows how:

```
Use the skill-lab skill
```

Or read [skills/skill-lab/SKILL.md](skills/skill-lab/SKILL.md) directly.

---

MIT License. See [LICENSE](LICENSE).
