# Publishing the Implementer Skill

## Directory Structure

```
your-repo/
├── README.md
├── skills/
│   └── implementer/
│       ├── SKILL.md
│       ├── evals/
│       │   ├── evals.json
│       │   └── grade.py
│       ├── scripts/
│       │   └── orchestrate.py
│       └── references/
│           ├── publishing.md    ← this file
│           └── dialectic-roles.md
```

## Steps to Publish

1. Create a GitHub repo (e.g., `your-name/claude-skills`)
2. Create the `skills/implementer/` directory tree
3. Copy `SKILL.md`, `evals/`, `scripts/`, and `references/` into it
4. Add a `skills.sh` listing at the repo root:

```sh
#!/bin/sh
echo "skills/implementer"
```

5. Push to GitHub

## Installing

Once published, users install with:

```bash
hermes skills tap add your-username/your-repo
hermes skills install your-username/your-repo/skills/implementer
```

Or via direct path for local testing:

```bash
claude --skill /path/to/implementer/
```

## Running the Orchestration Script

The `scripts/orchestrate.py` helper drives the loop programmatically:

```bash
python3 scripts/orchestrate.py "implement this plan: ..." [--max-loops 8]
```

It writes loop artifacts to `/tmp/implementer-loop/` and emits structured output
to `stdout` and `outputs/summary.json`.

## Running Evals

```bash
python3 evals/grade.py evals/evals.json /tmp/implementer-loop
```

The grader reads loop artifacts and reports which assertions passed/failed per test case.

## Versioning

- Increment `metadata.version` in SKILL.md frontmatter when making changes
- Document notable changes in the skill body (what changed, why, when)
- Use semver for releases (1.0.0, 1.1.0, 2.0.0)