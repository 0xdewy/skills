#!/usr/bin/env python3
"""
implementer/scripts/orchestrate.py

Drives the Implementer → Reviewer → Fixer loop.
Handles subagent completion signals, writes structured state,
emits human-readable progress to stdout.

Usage:
    python3 orchestrate.py "<task description>" [--max-loops N]

Outputs:
    /tmp/implementer-loop/outputs/summary.json  — structured machine-readable summary
    stdout                                        — human-readable progress
"""

import json
import os
import sys
import subprocess
import re
from pathlib import Path

WORKING_DIR = Path(os.environ.get("IMPLEMENTER_DIR", "/tmp/implementer-loop"))
MAX_LOOPS_DEFAULT = 8


def parse_args():
    args = sys.argv[1:]
    task = None
    max_loops = MAX_LOOPS_DEFAULT

    i = 0
    while i < len(args):
        if args[i] == "--max-loops" and i + 1 < len(args):
            max_loops = int(args[i + 1])
            i += 2
        elif args[i].startswith("--"):
            i += 1
        else:
            task = args[i]
            i += 1

    if not task:
        print("Usage: orchestrate.py '<task description>' [--max-loops N]")
        sys.exit(1)

    return task, max_loops


def ensure_dirs():
    (WORKING_DIR / "implementer").mkdir(parents=True, exist_ok=True)
    (WORKING_DIR / "reviewer").mkdir(parents=True, exist_ok=True)
    (WORKING_DIR / "fixer").mkdir(parents=True, exist_ok=True)
    (WORKING_DIR / "outputs").mkdir(parents=True, exist_ok=True)


def init_summary():
    summary = {
        "loop_count": 1,
        "max_loops": MAX_LOOPS_DEFAULT,
        "verdict": "IN_PROGRESS",
        "score": None,
        "files": [],
        "gaps": [],
        "summary": None
    }
    write_summary(summary)
    return summary


def write_summary(summary):
    with open(WORKING_DIR / "outputs" / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)


def spawn_implementer(task, loop_count, fixer_feedback=None):
    print(f"\n[{loop_count}] IMPLEMENTER: Starting implementation...")
    prompt = build_implementer_prompt(task, loop_count, fixer_feedback)
    result = subprocess.run(["claude", "--print", prompt],
                          capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(f"[{loop_count}] IMPLEMENTER: Done")
    if "IMPLEMENTER_DONE" not in output:
        print(f"[{loop_count}] IMPLEMENTER: WARNING — completion signal missing, respawning")
        return spawn_implementer(task, loop_count, fixer_feedback)
    return output


def build_implementer_prompt(task, loop_count, fixer_feedback=None):
    fixer_read = ""
    if loop_count > 1:
        fixer_path = WORKING_DIR / "fixer" / "fix-plan.md"
        if fixer_path.exists():
            fixer_read = f"\n\nIMPORTANT: Read /tmp/implementer-loop/fixer/fix-plan.md and address those specific issues. Do NOT re-implement from scratch."

    return f"""You are the Implementer for this iteration. Loop: {loop_count}.

ORIGINAL TASK:
{task}

WORKING DIRECTORY: /tmp/implementer-loop/

Read any existing context files in /tmp/implementer-loop/ before starting.{fixer_read}

Your job is to implement the plan fully. Produce:

1. All source code, scripts, configs needed
2. A README.md explaining how to build and run
3. TEST_RESULTS.md documenting what you tested manually
4. An IMPLEMENTATION_NOTES.md covering key decisions and why

Output everything to /tmp/implementer-loop/implementer/

IMPORTANT: Before declaring done, verify:
- The code compiles or runs without errors
- README instructions are accurate and complete
- All promised features are present

End your final message with exactly: IMPLEMENTER_DONE"""


def spawn_reviewer(task, loop_count):
    print(f"\n[{loop_count}] REVIEWER: Analyzing implementation...")
    prompt = build_reviewer_prompt(task, loop_count)
    result = subprocess.run(["claude", "--print", prompt],
                          capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(f"[{loop_count}] REVIEWER: Done")
    return output


def build_reviewer_prompt(task, loop_count):
    return f"""You are the Reviewer for this iteration. Loop: {loop_count}.

ORIGINAL TASK:
{task}

WORKING DIRECTORY: /tmp/implementer-loop/

Read everything in /tmp/implementer-loop/implementer/ thoroughly.

Your job is to critically analyze the implementation and determine if it is
10/10 ready for the user.

MANDATORY CHECKS — execute all of these, not just code inspection:
1. CORRECTNESS — Does it actually solve the stated task?
2. COMPLETENESS — Are all features from the plan present?
3. RUNS WITHOUT ERROR — Execute the code. Does it start and run without crashes?
4. TESTS PASS — Run any tests. Do they pass?
5. EDGE CASES — Try broken inputs. Does it fail gracefully?
6. CODE QUALITY — Are there bugs, anti-patterns, or security issues?
7. DOCUMENTATION — Is it clear how to run and use?

For each check: rate 0–10 with a one-sentence justification.
Compute overall score as the weighted average (correctness 30%, completeness 20%,
runs without error 20%, tests pass 10%, edge cases 10%, code quality 5%, docs 5%).

Write your full assessment to:
/tmp/implementer-loop/reviewer/assessment-loop{loop_count}.md

Format requirements:
- Rate every dimension explicitly
- For any dimension rated below 7, explain why
- If overall score < 10, list specific gaps in order of severity

End your final message with exactly:
REVIEWER_DONE: VERDICT={{DONE|NEEDS_WORK}} SCORE={{X}}/10"""


def parse_verdict(output):
    match = re.search(r"REVIEWER_DONE: VERDICT=(DONE|NEEDS_WORK) SCORE=(\d+)/10", output)
    if match:
        return match.group(1), int(match.group(2))
    return None, None


def spawn_fixer(task, loop_count):
    print(f"\n[{loop_count}] FIXER: Planning fixes...")
    prompt = build_fixer_prompt(task, loop_count)
    result = subprocess.run(["claude", "--print", prompt],
                          capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(f"[{loop_count}] FIXER: Done")
    if "FIXER_DONE" not in output:
        print(f"[{loop_count}] FIXER: WARNING — completion signal missing, respawning")
        return spawn_fixer(task, loop_count)
    return output


def build_fixer_prompt(task, loop_count):
    return f"""You are the Fixer for this iteration. Loop: {loop_count}.

ORIGINAL TASK:
{task}

WORKING DIRECTORY: /tmp/implementer-loop/

Read /tmp/implementer-loop/reviewer/assessment-loop{loop_count}.md to
understand what failed. Read any prior fix-plan.md files to avoid repeating fixes.

Your job is to analyze the failures and produce a targeted fix plan.

Write to: /tmp/implementer-loop/fixer/fix-plan.md

Format requirements — be exact:
## Problems Identified
1. [problem description — file:line or specific area]
   Why it fails: [one sentence]
   Fix needed: [specific change, not a vague direction]

## Fix Plan
For each problem above:
- Area: [file or module]
- Change: [the exact change needed]
- Why: [how this addresses the problem]

## Priority
Fix in this order: [1, 2, 3...]

The implementer must read your plan and make exactly the right changes without
guesswork. If a problem is "function X doesn't handle null", the fix is not
"add null handling" — it is "add null check before line Y, return error message Z".

End your final message with exactly: FIXER_DONE"""


def collect_implementer_files():
    impl_dir = WORKING_DIR / "implementer"
    files = []
    if impl_dir.exists():
        for f in impl_dir.rglob("*"):
            if f.is_file():
                files.append(str(f.relative_to(impl_dir)))
    return files


def extract_gaps(assessment_path):
    gaps = []
    try:
        with open(assessment_path) as f:
            content = f.read()
        gap_section = re.search(r"(?:specific gaps|gaps in order of severity|gaps identified)[:\n](.*?)(?:\n##|\Z)",
                               content, re.IGNORECASE | re.DOTALL)
        if gap_section:
            gap_text = gap_section.group(1).strip()
            for line in gap_text.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                    cleaned = re.sub(r"^[\d\.\-\*]+[\.\)\s]*", "", line).strip()
                    if cleaned:
                        gaps.append(cleaned)
            if not gaps:
                lines = [l.strip() for l in gap_text.split("\n") if l.strip()]
                gaps = [l for l in lines if len(l) > 10]
        if not gaps:
            score_match = re.search(r"(?:overall |final )?score[:\s]*(\d+)/10", content, re.IGNORECASE)
            gaps = [f"Reviewer assessment at {assessment_path} — see file for details"]
            if score_match:
                gaps.insert(0, f"Overall score: {score_match.group(1)}/10")
    except Exception:
        gaps = [f"Could not parse gaps from {assessment_path}"]
    return gaps


def write_final_summary(loop_count, verdict, score, summary_text, files, gaps=None):
    summary = {
        "loop_count": loop_count,
        "max_loops": MAX_LOOPS_DEFAULT,
        "verdict": verdict,
        "score": score,
        "files": files,
        "gaps": gaps or [],
        "summary": summary_text
    }
    write_summary(summary)
    return summary


def run_loop(task, max_loops):
    ensure_dirs()
    init_summary()
    loop_count = 1
    last_score = None

    while loop_count <= max_loops:
        print(f"\n{'='*60}")
        print(f"LOOP {loop_count}/{max_loops}")
        print(f"{'='*60}")

        impl_output = spawn_implementer(task, loop_count)
        print(f"[{loop_count}] Implementation complete")

        rev_output = spawn_reviewer(task, loop_count)
        verdict, score = parse_verdict(rev_output)

        if verdict is None:
            print(f"[{loop_count}] REVIEWER: Could not parse verdict — assuming NEEDS_WORK")
            verdict = "NEEDS_WORK"
            score = 0

        last_score = score
        print(f"[{loop_count}] Review verdict: {verdict} ({score}/10)")

        if verdict == "DONE":
            files = collect_implementer_files()
            summary_str = f"Built and validated after {loop_count} loop(s). Score: {score}/10."
            write_final_summary(loop_count, "DONE", score, summary_str, files)
            print(f"\nDONE: implementer delivered after {loop_count} loop(s), score {score}/10, status DONE, files at {WORKING_DIR}/implementer/")
            return

        if loop_count >= max_loops:
            rev_file = WORKING_DIR / "reviewer" / f"assessment-loop{loop_count}.md"
            gaps = extract_gaps(rev_file) if rev_file.exists() else []
            write_final_summary(loop_count, "PARTIAL", last_score,
                              f"Stopped after reaching max loops ({max_loops}). {loop_count - 1} fix attempt(s) made.",
                              [], gaps=gaps)
            print(f"\nDONE: implementer stopped after {max_loops} loops (cap), score {last_score}/10, partial — gaps remain")
            print(f"Partial summary at: {WORKING_DIR}/outputs/summary.json")
            return

        print(f"[{loop_count}] Reviewer found issues — spawning Fixer")
        spawn_fixer(task, loop_count)
        loop_count += 1
        print(f"[{loop_count}] Moving to next loop")


if __name__ == "__main__":
    task, max_loops = parse_args()
    run_loop(task, max_loops)