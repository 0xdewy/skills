# Example Skill: timestamp-formatter

This is a complete, annotated example of a well-written skill. Read it before
writing your first SKILL.md to calibrate what "good" looks like. The skill is
real and runnable — no invented APIs or imaginary dependencies.

---

## What it does

`timestamp-formatter` scans a text file for mixed-format timestamps (Unix epoch,
ISO 8601, US date strings, etc.) and rewrites them all as ISO 8601 UTC. It
writes the normalized file to `./outputs/<original-filename>`.

---

## The SKILL.md

```markdown
---
name: timestamp-formatter
description: >-
  Normalize mixed-format timestamps in a file to ISO 8601 UTC. TRIGGER on:
  "normalize timestamps", "convert dates to ISO", "fix timestamp formats",
  "standardize dates in this file", "reformat all dates". SKIP on: casual
  questions about dates or time zones that don't involve file processing, or
  requests to format a single date string inline (answer those directly).
license: MIT
metadata:
  author: your-github-username
  version: 1.0.0
  category: data
  tags:
    - timestamps
    - data-cleaning
    - iso8601
---

# Timestamp Formatter

Normalizes mixed-format timestamps in a file to ISO 8601 UTC. Useful as a
preprocessing step before ingesting logs, CSVs, or exported data into pipelines
that expect a consistent date format.

**Why this is a skill:** data teams run this repeatedly on exports from
different source systems. Encoding it as a skill ensures the normalization rules
(which formats to detect, how to handle ambiguous dates like 01/02/03) are
applied consistently across sessions and users.

**Output format:** normalized file at `./outputs/<original-filename>`.
Chains naturally with the `data-analysis` skill, which expects input at
`./outputs/`.

---

## Phase 1: Resolve the input

Accept the file path from the invocation prompt. If not provided, ask once:
"Which file should I normalize timestamps in?"

Check the file exists. If the format is a structured type (CSV, JSON, NDJSON),
identify which columns contain timestamps. For plain text/logs, scan all lines.

---

## Phase 2: Normalize

Run `scripts/format_timestamps.py` with the resolved file path:

```bash
python scripts/format_timestamps.py <input-file> ./outputs/<filename>
```

The script handles detection and conversion. It outputs a summary to stdout:
- Count of timestamps converted
- Count of timestamps it couldn't parse (logged to `./outputs/skipped.txt`)
- Any ambiguous formats it resolved (e.g., "01/02/03 → 2003-01-02, assumed YMD")

Read the stdout summary. If skipped count > 0, report them to the user and
explain why they were skipped.

---

## Phase 3: Report

Output:

```
DONE: <N> timestamps normalized → ./outputs/<filename>
Skipped: <M> (see ./outputs/skipped.txt)
Ambiguous resolutions: <list any>
```

This completion signal is machine-parseable — callers in a pipeline can detect
`DONE:` on the last line to confirm success.
```

---

## Annotations

### Why the description is structured this way

The TRIGGER/SKIP structure prevents two failure modes:
- **Undertriggering:** "normalize timestamps" alone is too vague. The explicit
  trigger phrases cover realistic user phrasing.
- **Overtriggering:** "fix dates" could match many casual questions. The SKIP
  clause handles "what time zone is Tokyo in?" — answer directly, don't invoke
  the skill.

### Why "Why this is a skill" appears in the body

It establishes intent for anyone reading the skill (or improving it). It also
helps Claude contextualize edge cases: "recurring, consistent across sessions"
tells Claude to apply the same rules each time rather than improvising.

### Why the script is called rather than inlined

`format_timestamps.py` would be 60–80 lines if written inline as instructions.
It would also be reinvented slightly differently each run. Bundling it as a
script makes the behavior deterministic and saves token cost.

### Why "chains with data-analysis" is documented

Composition only works if callers know the contract. The output path
(`./outputs/`) and downstream skill name are the contract. Without this, a
pipeline author has to read the skill carefully to figure out where output lands.

### Why Phase 3 ends with a parseable line

Prose summaries like "I've finished normalizing the file" are hard for
orchestrators to detect reliably. `DONE: N timestamps normalized → ./path` is
greppable. A loop or schedule agent can check for this line to confirm success
before moving to the next step.

---

## What evals would look like

`evals/evals.json` for this skill would contain test cases like:

```json
[
  {
    "id": 1,
    "prompt": "normalize timestamps in tests/fixtures/logs.txt",
    "expected_output": "ISO 8601 timestamps in outputs/logs.txt, DONE line in output",
    "expectations": [
      "outputs/logs.txt exists",
      "output contains 'DONE:'",
      "no Unix epoch strings remain in outputs/logs.txt"
    ]
  },
  {
    "id": 2,
    "prompt": "what time is it in Tokyo?",
    "expected_output": "Direct answer, skill NOT invoked",
    "expectations": [
      "no file written to outputs/",
      "response does not mention timestamp-formatter"
    ]
  }
]
```

The second test case validates the SKIP behavior — that the skill doesn't fire
on casual time-zone questions. Testing negative trigger cases is as important as
testing positive ones.

---

## Directory layout for this skill

```
timestamp-formatter/
├── SKILL.md
├── scripts/
│   └── format_timestamps.py   ← handles detection + conversion
├── evals/
│   └── evals.json             ← test cases including SKIP cases
└── references/
    └── format-detection.md    ← reference table of ~40 formats detected
```

`references/format-detection.md` is loaded only when the user asks "what
formats can you detect?" — not on every invocation. The SKILL.md tells the
skill: "For the full list of supported input formats, see
`references/format-detection.md`."
