# Project Type Patterns

Loaded by agentify during Phase 3 (Design) to determine type-specific
documentation architecture. Read the section matching the `project_type`
from analysis.json.

---

## monorepo

**Detection signals:** multiple `package.json` / `Cargo.toml` / `pyproject.toml`
at non-root paths, or root-level `pnpm-workspace.yaml` / `Cargo.toml` with
`[workspace]` / `go.work` / `nx.json` / `lerna.json`.

**Doc architecture:**
- Root `CLAUDE.md`: shared standards only (commit format, PR template, shared tooling)
- Root `docs/OVERVIEW.md`: monorepo map — what each package/service does, how
  packages relate, shared infrastructure
- Per-package `CLAUDE.md` (if packages are large): package-specific commands
  and conventions. Use `claudeMdExcludes` in `.claude/settings.local.json` to
  prevent root CLAUDE.md loading when inside a specific package
- `docs/{service-name}.md`: per-service architecture

**Monorepo context management:**
- If team CLAUDE.md files from other packages get picked up, use `.claude/settings.local.json`:
  ```json
  {
    "claudeMdExcludes": ["**/other-team/CLAUDE.md", "**/legacy/.claude/rules/**"]
  }
  ```
- This prevents contamination from unrelated team conventions

**Rules files:** one per cross-cutting domain (testing conventions shared
across packages, shared CI/CD patterns). Package-specific rules go in the
package's own `.claude/rules/`.

**Key OVERVIEW sections:** service dependency graph (which services call which),
shared libraries map, deployment topology.

### Phase 4 Execution — Monorepo Pattern

When `project_type == "monorepo"`, generate files in this order:

1. **Root CLAUDE.md** (≤200 lines) — shared standards, monorepo tooling,
   inter-service conventions only. No service-specific content in this file.
2. **Root docs/OVERVIEW.md** (≤400 lines) — service map with Mermaid `graph TD`
   showing service relationships and inter-service data flows.
3. **docs/{service}.md** (≤300 lines each) — one per entry in `service_packages`
   from analysis.json (dirs detected to have their own package manifest).
   Cover: purpose, entry points, key commands specific to this service.
4. **Root .claude/rules/** — shared conventions across all services.
5. **docs/NAVIGATION.md** — explains the two-level hierarchy.
6. **.claude/context-map.md** — maps everything (LAST, after all other files).
7. **Coordination dirs** — apply if `has_multiagent_signals`, same as Standard.

If `service_packages` is empty (no per-package manifests found), fall back to
the Standard Pattern and note in Phase 3 that monorepo detection was ambiguous.

---

## service

**Detection signals:** one `package.json` / `Cargo.toml` / `pyproject.toml`
at root, clear layered directory structure (api/, service/, model/, repository/
or equivalent), no sub-packages.

**Doc architecture:**
- `CLAUDE.md`: project purpose, commands, pointer map
- `docs/OVERVIEW.md`: the layer architecture (API → Service → Repository → DB)
- `docs/api.md`: handler/route conventions
- `docs/services.md`: business logic patterns, transaction handling
- `docs/models.md` or `docs/db.md`: data model, ORM patterns, migrations
- `.claude/rules/api.md`: route/handler conventions (path-scoped)
- `.claude/rules/testing.md`: test patterns (path-scoped)

**Key OVERVIEW diagram:** layered architecture top-down showing request flow
from API → Service → Repository → Database.

---

## webapp

**Detection signals:** React/Vue/Angular/Svelte/Next/Nuxt dependencies,
`pages/` or `app/` directory, `public/` or `static/` directory.

**Doc architecture:**
- `CLAUDE.md`: purpose, commands (dev server, build, test), pointer map
- `docs/OVERVIEW.md`: frontend/backend split if full-stack, page/route map,
  state management approach, key third-party integrations (auth, payments, etc.)
- `docs/components.md`: component patterns, design system usage, props conventions
- `docs/state.md`: state management patterns (Redux, Zustand, Pinia, etc.)
- `docs/api.md` (if has backend): API layer conventions
- `.claude/rules/frontend.md`: component patterns (path-scoped: `src/components/**`)
- `.claude/rules/testing.md`: test patterns
- `.claude/rules/api.md` (if has backend): API conventions

**Key OVERVIEW diagram:** page/route hierarchy for frontend; request flow for
any backend; integration map for external services.

---

## library

**Detection signals:** no entry point / main server, `src/` contains only
exported functions/classes, has `lib/` or `pkg/` output target, docs/ may
have API reference.

**Doc architecture:**
- `CLAUDE.md`: what the library does, install + usage snippet (2-3 lines),
  build + test commands, pointer map
- `docs/OVERVIEW.md`: public API surface (the exported functions/classes/types),
  design philosophy, key abstractions, how pieces fit together
- `docs/api-reference.md`: full public API documentation (this can exceed 300
  lines for large libraries — split by module if needed)
- `docs/internals.md`: internal architecture for contributors
- `docs/examples.md`: 3-5 usage examples
- `.claude/rules/public-api.md`: conventions for the public API surface
- `.claude/rules/testing.md`: test patterns

**Key OVERVIEW section:** the public API surface is the most important content
— an agent contributing to a library needs to know what's exported and why.

---

## cli

**Detection signals:** `main.go` / `cmd/` / `src/cli/` / `bin/` entry,
`cobra` / `click` / `clap` / `argparse` / `yargs` dependency, `Makefile`
with install target.

**Doc architecture:**
- `CLAUDE.md`: what the CLI does, install command, 3-5 most common usage
  examples (the actual commands), build + test commands, pointer map
- `docs/OVERVIEW.md`: command taxonomy (all commands in a table: command,
  description, key flags), configuration file format, plugin system if any
- `docs/{command-group}.md`: one file per logical command group
  (e.g., `docs/auth-commands.md`, `docs/deploy-commands.md`)
- `.claude/rules/cli.md`: argument parsing patterns, output formatting,
  exit code conventions (path-scoped: `cmd/**`, `**/commands/**`)

**Key OVERVIEW section:** the command taxonomy table. An agent adding a new
command needs to see all existing commands to place the new one correctly.

---

## data_pipeline

**Detection signals:** `dbt/` / `airflow/` / `prefect/` / `dagster/` patterns,
`transforms/` or `pipelines/` directory, ETL naming, data format files
(`.sql`, `.yaml` workflow definitions).

**Doc architecture:**
- `CLAUDE.md`: what data flows through the pipeline, how to run it, pointer map
- `docs/OVERVIEW.md`: end-to-end data flow diagram (source → transform → sink),
  data lineage, schedule, SLAs
- `docs/sources.md`: each data source — schema, access pattern, freshness
- `docs/transforms.md`: transformation patterns, key business logic rules
- `docs/sinks.md`: output destinations and formats
- `docs/operations.md`: how to backfill, debug failures, monitor
- `.claude/rules/transforms.md`: SQL/Python transform conventions
- `.claude/rules/testing.md`: data test patterns

---

## unknown

When `project_type` is `unknown`, use the service pattern as a default but
note it in the documentation plan. If the repo has:
- Multiple entry points → treat as service or webapp
- No clear main entry → treat as library
- Only scripts → create a simpler structure (just CLAUDE.md + context-map)

Always inspect the README and git history before deciding — the commit
messages often reveal what type of project this is.

---

## plugin

**Detection signals:** `.vsixmanifest` / `extension.js` / `manifest.json` in
root or top-level dir, `src/extension.ts` entry point, VSCode/Cursor/JetBrains
extension artifacts.

**Doc architecture:**
- `CLAUDE.md`: what the plugin does, install command, activation events, commands
  exposed, pointer map
- `docs/OVERVIEW.md`: extension lifecycle (activation → deactivation), contribution
  points, key API integrations, command taxonomy
- `docs/commands.md`: all commands with their handlers and keybindings
- `docs/providers.md`: tree views, webviews, language features
- `.claude/rules/extension.md`: activation event patterns, contribution point
  conventions (path-scoped: `src/**`, `**/extension.*`)
- `.claude/rules/testing.md`: extension test patterns (vscode-test, e2e tests)

**Key OVERVIEW section:** the activation flow — when does the extension start,
what features does it register, and how do they interact?

---

## mobile

**Detection signals:** React Native (`ios/`, `android/` dirs), Flutter (`lib/`,
`pubspec.yaml`), Expo (`app.json`, `eas.json`), Capacitor.

**Doc architecture:**
- `CLAUDE.md`: what the app does, platform targets, emulator commands, pointer map
- `docs/OVERVIEW.md`: navigation structure (stack/tab/drawer map), platform-specific
  code organization, state management approach
- `docs/screens.md`: screen components, navigation params, deep links
- `docs/native.md`: native modules, platform channels, bridging code
- `.claude/rules/mobile.md`: component patterns, safe area handling, platform
  detection (path-scoped: `src/**`, `lib/**`, `app/**`)
- `.claude/rules/testing.md`: component tests, e2e tests, platform-specific tests

**Key OVERVIEW section:** the navigation tree and platform bridge diagram.

---

## agent-skill

**Detection signals:** Contains `SKILL.md` or `*.skill.md` files, `.claude/`
configuration directory, `/init` style project structure, no traditional build
system, only markdown and configuration files.

**Doc architecture:**
- `CLAUDE.md`: what the skill/agent does, its trigger conditions, key workflows
- `docs/OVERVIEW.md`: skill architecture (what it orchestrates, subagents, hooks),
  configuration surface, MCP server integrations
- `docs/workflows.md`: the step-by-step workflows the skill executes
- `docs/config.md`: configuration options, settings, environment variables
- `.claude/rules/skills.md`: skill authoring conventions, metadata standards
  (path-scoped: `**/*.md`, `**/SKILL.md`)
- `.claude/rules/scripts.md`: scripting conventions for skill scripts

**Key OVERVIEW section:** the trigger logic — what prompts activate this skill,
and the decision tree it follows after activation.
