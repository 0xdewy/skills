# Publishing Skills to GitHub

## Repo Structure

Skills are discovered from GitHub repos by path convention. The standard
layout that works with `hermes skills tap` and `skills.sh` is:

```
your-repo/
├── README.md
└── skills/
    ├── skill-one/
    │   └── SKILL.md
    ├── skill-two/
    │   ├── SKILL.md
    │   ├── references/
    │   └── scripts/
    └── skill-creator/
        └── SKILL.md
```

Skills live in a `skills/` subdirectory. Each skill is a directory named after
it, containing `SKILL.md` and optional resources.

## Setting Up a New Skills Repo

```bash
mkdir my-skills && cd my-skills
git init
mkdir -p skills/my-first-skill

# Write your SKILL.md
cat > skills/my-first-skill/SKILL.md << 'EOF'
---
name: my-first-skill
description: >-
  What it does, and when to use it.
license: MIT
metadata:
  author: your-github-username
  version: 1.0.0
  category: productivity
  tags:
    - useful-tag
---

# My First Skill
...
EOF

git add .
git commit -m "Add my-first-skill"

# Push to GitHub (replace with your repo)
gh repo create your-username/my-skills --public --push
```

## How Others Install Your Skills

### Option 1: Add as a tap (recommended for multiple skills)

A tap lets people browse and install any skill from your repo:

```bash
# Add the tap
hermes skills tap add your-username/my-skills

# Browse your skills
hermes skills search

# Install a specific skill
hermes skills install your-username/my-skills/skills/skill-creator
```

### Option 2: Install directly by path

No tap needed for one-off installs:

```bash
hermes skills install your-username/my-skills/skills/skill-creator
```

### Option 3: skills.sh listing

To list on skills.sh (broader discovery), submit your skill at skills.sh.
Once listed, people can find and install it through the main marketplace.

## Versioning

Update `metadata.version` in frontmatter when making significant changes.
Use semantic versioning (MAJOR.MINOR.PATCH):
- PATCH: typo fixes, clarification
- MINOR: new capabilities, backward-compatible
- MAJOR: breaking changes to interface or behavior

## Trust Levels

Skills installed from GitHub have "community" trust by default. Trust levels:
- **builtin**: Ships with the agent (not applicable to external skills)
- **trusted**: Repos in a trusted list
- **community**: Everyone else — requires user confirmation on install

Your users will see a confirmation prompt before installing. Make sure your
SKILL.md doesn't contain anything that would surprise them.

## README Template

Include a README so people know what your repo contains:

```markdown
# My Skills

A collection of Claude skills for [domain/purpose].

## Install

```bash
hermes skills tap add your-username/my-skills
```

## Skills

| Skill | Description |
|-------|-------------|
| [skill-creator](skills/skill-creator/) | Create and publish Claude skills |
| [other-skill](skills/other-skill/) | Description here |

## Usage

After adding the tap, install any skill:
```bash
hermes skills install your-username/my-skills/skills/SKILL_NAME
```
```

## Updating an Installed Skill

```bash
# Force reinstall to get latest version
hermes skills install --force your-username/my-skills/skills/skill-creator
```
