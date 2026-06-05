#!/usr/bin/env python3
"""
implementer/scripts/orchestrate.py

Drives the Implementer -> Correctness Reviewer -> Succinctness Reviewer -> Fixer loop.
Handles subagent completion signals, writes structured state each loop,
emits human-readable progress to stdout.

Usage:
    python3 orchestrate.py "<task description>" [--max-loops N]

Outputs:
    /tmp/implementer-loop/outputs/summary.json  -- structured machine-readable summary
    stdout                                        -- human-readable progress
"""

import json
import os
import sys
import subprocess
import re
from pathlib import Path

WORKING_DIR = Path(os.environ.get("IMPLEMENTER_DIR", "/tmp/implementer-loop"))
MAX_LOOPS_DEFAULT = 8
MAX_RESPAWNS = 2


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


def init_summary(max_loops):
    summary = {
        "loop_count": 1,
        "max_loops": max_loops,
        "verdict": "IN_PROGRESS",
        "correctness_score": None,
        "succinctness_score": None,
        "files": [],
        "gaps": [],
        "skeptic_result": None,
        "summary": None
    }
    write_summary(summary)
    return summary


def write_summary(summary):
    with open(WORKING_DIR / "outputs" / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)


def update_loop_summary(loop_count, max_loops, corr_verdict, corr_score, succ_verdict, succ_score, skeptic):
    summary = {
        "loop_count": loop_count,
        "max_loops": max_loops,
        "verdict": "IN_PROGRESS",
        "correctness_score": corr_score,
        "succinctness_score": succ_score,
        "correctness_verdict": corr_verdict,
        "succinctness_verdict": succ_verdict,
        "skeptic_result": skeptic,
        "files": [],
        "gaps": [],
        "summary": None
    }
    write_summary(summary)


# ─── Implementer ───────────────────────────────────────────────────────────

def spawn_implementer(task, loop_count, _respawn_count=0):
    print(f"\n[{loop_count}] IMPLEMENTER: Starting implementation...")
    prompt = build_implementer_prompt(task, loop_count)
    result = subprocess.run(["claude", "--print", prompt],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{loop_count}] IMPLEMENTER: WARNING - subprocess exited with code {result.returncode}")
    output = result.stdout + result.stderr
    print(f"[{loop_count}] IMPLEMENTER: Done")
    if "IMPLEMENTER_DONE" not in output:
        if _respawn_count >= MAX_RESPAWNS:
            print(f"[{loop_count}] IMPLEMENTER: ERROR - max respawns ({MAX_RESPAWNS}) reached, continuing anyway")
            return output
        print(f"[{loop_count}] IMPLEMENTER: WARNING - completion signal missing, respawning ({_respawn_count + 1}/{MAX_RESPAWNS})")
        return spawn_implementer(task, loop_count, _respawn_count + 1)
    return output


def build_implementer_prompt(task, loop_count):
    fixer_read = ""
    if loop_count > 1:
        fixer_path = WORKING_DIR / "fixer" / "fix-plan.md"
        if fixer_path.exists():
            fixer_read = ("\n\nIMPORTANT: Read /tmp/implementer-loop/fixer/fix-plan.md and "
                         "address those specific issues. Do NOT re-implement from scratch.")

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


# ─── Correctness Reviewer ──────────────────────────────────────────────────

def spawn_correctness_reviewer(task, loop_count, _respawn_count=0):
    print(f"\n[{loop_count}] CORRECTNESS-REVIEWER: Analyzing implementation...")
    prompt = build_correctness_reviewer_prompt(task, loop_count)
    result = subprocess.run(["claude", "--print", prompt],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{loop_count}] CORRECTNESS-REVIEWER: WARNING - subprocess exited with code {result.returncode}")
    output = result.stdout + result.stderr
    print(f"[{loop_count}] CORRECTNESS-REVIEWER: Done")
    if "CORRECTNESS_DONE:" not in output:
        if _respawn_count >= MAX_RESPAWNS:
            print(f"[{loop_count}] CORRECTNESS-REVIEWER: ERROR - max respawns ({MAX_RESPAWNS}) reached")
            return output
        print(f"[{loop_count}] CORRECTNESS-REVIEWER: WARNING - completion signal missing, respawning ({_respawn_count + 1}/{MAX_RESPAWNS})")
        return spawn_correctness_reviewer(task, loop_count, _respawn_count + 1)
    return output


def build_correctness_reviewer_prompt(task, loop_count):
    return f"""You are the Correctness Reviewer for this iteration. Loop: {loop_count}.

ORIGINAL TASK:
{task}

WORKING DIRECTORY: /tmp/implementer-loop/

Read everything in /tmp/implementer-loop/implementer/ thoroughly.

MANDATORY CHECKS -- execute all of them:

SKEPTIC PASS (always run first -- read only the implementation output in
/tmp/implementer-loop/implementer/, NOT the original task above):
0. Find the single strongest flaw, gap, internal contradiction, unsupported
   claim, or dangerous unstated assumption in this output. Quote the exact
   phrase. Explain why it is flawed in one sentence. If -- after genuinely
   trying -- you cannot find a remaining flaw worth raising, output exactly:
   Skeptic: CLEAN
   If you do find a flaw, output as:
   Skeptic: FLAW: "[exact quote]" REASON: [one sentence]

CONTEXT-AWARE PASS:
1. CORRECTNESS -- Does it actually solve the stated task?
2. COMPLETENESS -- Are all features from the plan present?
3. RUNS WITHOUT ERROR -- Execute the code. Does it start and run without crashes?
4. TESTS PASS -- Run any tests. Do they pass?
5. EDGE CASES -- Try broken inputs. Does it fail gracefully?
6. CODE QUALITY -- Are there bugs, anti-patterns, or security issues?
7. DOCUMENTATION -- Is it clear how to run and use?

For each check: rate 0-10 with a one-sentence justification.
Compute overall score as weighted average (correctness 30%, completeness 20%,
runs without error 20%, tests pass 10%, edge cases 10%, code quality 5%, docs 5%).

THE SKEPTIC PASS OVERRIDES: if Skeptic found a flaw (SKEPTIC=FLAW), your
VERDICT MUST be NEEDS_WORK regardless of other scores. Only when
SKEPTIC=CLEAN AND all dimensions score >= 7 can VERDICT=DONE.

Write your full assessment to:
/tmp/implementer-loop/reviewer/assessment-loop{loop_count}.md

Format requirements:
- Skeptic pass result first (Skeptic: CLEAN or Skeptic: FLAW: "..." REASON: ...)
- Rate every applicable dimension explicitly
- For any dimension rated below 7, explain why
- If overall score < 10, list specific gaps in order of severity

End your final message with exactly:
CORRECTNESS_DONE: SKEPTIC={{FLAW|CLEAN}} VERDICT={{DONE|NEEDS_WORK}} SCORE={{X}}/10"""


def parse_correctness_verdict(output):
    match = re.search(
        r"correctness_done:\s*skeptic\s*=\s*(flaw|clean)\s*verdict\s*=\s*(done|needs_work)\s*score\s*=\s*(\d+)",
        output,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1).upper(), match.group(2).upper(), int(match.group(3))
    return None, None, None


# ─── Succinctness Reviewer ─────────────────────────────────────────────────

def spawn_succinctness_reviewer(task, loop_count, _respawn_count=0):
    print(f"\n[{loop_count}] SUCCINCTNESS-REVIEWER: Hunting bloat...")
    prompt = build_succinctness_reviewer_prompt(loop_count)
    result = subprocess.run(["claude", "--print", prompt],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{loop_count}] SUCCINCTNESS-REVIEWER: WARNING - subprocess exited with code {result.returncode}")
    output = result.stdout + result.stderr
    print(f"[{loop_count}] SUCCINCTNESS-REVIEWER: Done")
    if "SUCCINCTNESS_DONE:" not in output:
        if _respawn_count >= MAX_RESPAWNS:
            print(f"[{loop_count}] SUCCINCTNESS-REVIEWER: ERROR - max respawns ({MAX_RESPAWNS}) reached")
            return output
        print(f"[{loop_count}] SUCCINCTNESS-REVIEWER: WARNING - completion signal missing, respawning ({_respawn_count + 1}/{MAX_RESPAWNS})")
        return spawn_succinctness_reviewer(task, loop_count, _respawn_count + 1)
    return output


def build_succinctness_reviewer_prompt(loop_count):
    return f"""You are the Succinctness Reviewer for this iteration. Loop: {loop_count}.

WORKING DIRECTORY: /tmp/implementer-loop/

Read everything in /tmp/implementer-loop/implementer/ thoroughly.
Also read /tmp/implementer-loop/reviewer/assessment-loop{loop_count}.md
to avoid re-flagging issues the Correctness Reviewer already found.

Your job: make this code as minimal as possible without losing functionality.

MANDATORY CHECKS:
1. DUPLICATION -- Is the same logic expressed in two or more places? Flag each
   instance with file:line pairs.
2. DEAD CODE -- Unused imports, unreachable branches, commented-out blocks,
   variables assigned but never read, functions never called.
3. OVER-ABSTRACTION -- Factories that produce a single class, interfaces with
   only one implementation, wrappers that add no value, classes with one
   method that could be a function.
4. VERBOSE IDIOMS -- Multi-line boilerplate that a builtin or library function
   already provides. Redundant variable assignments. Unnecessary intermediate
   variables.
5. FILE BLoat -- Can any file be merged into another? Can any file be deleted
   entirely without loss?

For each check: rate 0-10 with a one-sentence justification.
If you find nothing to flag on a check, score it 10 and write "Nothing found."

Score is the simple average of the five dimensions.
If any dimension scores below 7, VERDICT=NEEDS_WORK.
If all dimensions score 7+, VERDICT=DONE.

Write your full assessment to:
/tmp/implementer-loop/reviewer/succinctness-loop{loop_count}.md

Format requirements:
- Score each dimension (Duplication: X/10 -- justification)
- List every DRY violation, dead code block, or over-abstraction with file:line
- For each finding, state what to delete or merge

End your final message with exactly:
SUCCINCTNESS_DONE: VERDICT={{DONE|NEEDS_WORK}} SCORE={{X}}/10"""


def parse_succinctness_verdict(output):
    match = re.search(
        r"succinctness_done:\s*verdict\s*=\s*(done|needs_work)\s*score\s*=\s*(\d+)",
        output,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1).upper(), int(match.group(2))
    return None, None


# ─── Fixer ─────────────────────────────────────────────────────────────────

def spawn_fixer(task, loop_count, _respawn_count=0):
    print(f"\n[{loop_count}] FIXER: Planning fixes...")
    prompt = build_fixer_prompt(task, loop_count)
    result = subprocess.run(["claude", "--print", prompt],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[{loop_count}] FIXER: WARNING - subprocess exited with code {result.returncode}")
    output = result.stdout + result.stderr
    print(f"[{loop_count}] FIXER: Done")
    if "FIXER_DONE" not in output:
        if _respawn_count >= MAX_RESPAWNS:
            print(f"[{loop_count}] FIXER: ERROR - max respawns ({MAX_RESPAWNS}) reached, continuing anyway")
            return output
        print(f"[{loop_count}] FIXER: WARNING - completion signal missing, respawning ({_respawn_count + 1}/{MAX_RESPAWNS})")
        return spawn_fixer(task, loop_count, _respawn_count + 1)
    return output


def build_fixer_prompt(task, loop_count):
    return f"""You are the Fixer for this iteration. Loop: {loop_count}.

ORIGINAL TASK:
{task}

WORKING DIRECTORY: /tmp/implementer-loop/

Read BOTH review files:
- /tmp/implementer-loop/reviewer/assessment-loop{loop_count}.md
- /tmp/implementer-loop/reviewer/succinctness-loop{loop_count}.md

Also read any prior fix-plan.md files to avoid repeating fixes.

Your job is to analyze all failures from both reviewers and produce ONE
unified fix plan. Address correctness issues and succinctness issues together.

Write to: /tmp/implementer-loop/fixer/fix-plan.md

Format requirements -- be exact:
## Problems Identified
1. [problem description -- file:line or specific area]
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
"add null handling" -- it is "add null check before line Y, return error message Z".

End your final message with exactly: FIXER_DONE"""


# ─── Gap extraction ────────────────────────────────────────────────────────

def extract_gaps_from_files(loop_count):
    gaps = []

    assessment_path = WORKING_DIR / "reviewer" / f"assessment-loop{loop_count}.md"
    if assessment_path.exists():
        gaps.extend(_extract_gaps(assessment_path, "Correctness"))

    succinctness_path = WORKING_DIR / "reviewer" / f"succinctness-loop{loop_count}.md"
    if succinctness_path.exists():
        gaps.extend(_extract_gaps(succinctness_path, "Succinctness"))

    return gaps if gaps else ["No specific gaps extracted from review files"]


def _extract_gaps(filepath, reviewer_type):
    gaps = []
    try:
        with open(filepath) as f:
            content = f.read()
        gap_section = re.search(
            r"(?:specific gaps|gaps in order of severity|gaps identified)[:\n](.*?)(?:\n##|\Z)",
            content, re.IGNORECASE | re.DOTALL
        )
        if gap_section:
            gap_text = gap_section.group(1).strip()
            for line in gap_text.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                    cleaned = re.sub(r"^[\d\.\-\*]+[\.\)\s]*", "", line).strip()
                    if cleaned:
                        gaps.append(f"[{reviewer_type}] {cleaned}")
            if not gaps:
                lines = [l.strip() for l in gap_text.split("\n") if l.strip()]
                gaps = [f"[{reviewer_type}] {l}" for l in lines if len(l) > 10]
        if not gaps:
            score_match = re.search(r"(?:overall |final )?score[:\s]*(\d+)/10", content, re.IGNORECASE)
            if score_match:
                gaps.append(f"[{reviewer_type}] Overall score: {score_match.group(1)}/10")
            gaps.append(f"[{reviewer_type}] See {filepath} for full assessment")
    except Exception:
        gaps.append(f"[{reviewer_type}] Could not parse {filepath}")
    return gaps


# ─── Collect implementer files ─────────────────────────────────────────────

def collect_implementer_files():
    impl_dir = WORKING_DIR / "implementer"
    files = []
    if impl_dir.exists():
        for f in impl_dir.rglob("*"):
            if f.is_file():
                files.append(str(f.relative_to(impl_dir)))
    return files


# ─── Final summary ─────────────────────────────────────────────────────────

def write_final_summary(loop_count, max_loops, verdict, corr_score, succ_score,
                        summary_text, files, gaps=None, skeptic=None):
    summary = {
        "loop_count": loop_count,
        "max_loops": max_loops,
        "verdict": verdict,
        "correctness_score": corr_score,
        "succinctness_score": succ_score,
        "skeptic_result": skeptic,
        "files": files,
        "gaps": gaps or [],
        "summary": summary_text
    }
    write_summary(summary)
    return summary


# ─── Main loop ─────────────────────────────────────────────────────────────

def run_loop(task, max_loops):
    ensure_dirs()
    init_summary(max_loops)
    loop_count = 1
    last_corr_score = None
    last_succ_score = None
    last_skeptic = None

    while loop_count <= max_loops:
        print(f"\n{'='*60}")
        print(f"LOOP {loop_count}/{max_loops}")
        print(f"{'='*60}")

        # Phase 3: Implement
        impl_output = spawn_implementer(task, loop_count)
        print(f"[{loop_count}] Implementation complete")

        # Phase 4a: Correctness Review
        corr_output = spawn_correctness_reviewer(task, loop_count)
        corr_skeptic, corr_verdict, corr_score = parse_correctness_verdict(corr_output)

        if corr_verdict is None:
            print(f"[{loop_count}] CORRECTNESS-REVIEWER: Could not parse verdict - assuming NEEDS_WORK")
            corr_verdict = "NEEDS_WORK"
            corr_score = 0
            corr_skeptic = "UNKNOWN"

        last_corr_score = corr_score
        last_skeptic = corr_skeptic
        print(f"[{loop_count}] Correctness review: {corr_verdict} ({corr_score}/10) Skeptic: {corr_skeptic}")

        # Phase 4b: Succinctness Review
        succ_output = spawn_succinctness_reviewer(task, loop_count)
        succ_verdict, succ_score = parse_succinctness_verdict(succ_output)

        if succ_verdict is None:
            print(f"[{loop_count}] SUCCINCTNESS-REVIEWER: Could not parse verdict - assuming NEEDS_WORK")
            succ_verdict = "NEEDS_WORK"
            succ_score = 0

        last_succ_score = succ_score
        print(f"[{loop_count}] Succinctness review: {succ_verdict} ({succ_score}/10)")

        # Update summary.json after each loop for crash-resilience
        update_loop_summary(loop_count, max_loops, corr_verdict, corr_score,
                           succ_verdict, succ_score, corr_skeptic)

        # Phase 5: Loop Control - both reviewers must return DONE
        both_done = (corr_verdict == "DONE" and succ_verdict == "DONE")

        if both_done:
            files = collect_implementer_files()
            summary_str = (f"Built, validated, and refined after {loop_count} loop(s). "
                          f"Correctness: {corr_score}/10. Succinctness: {succ_score}/10.")
            write_final_summary(loop_count, max_loops, "DONE", corr_score, succ_score,
                               summary_str, files, skeptic=corr_skeptic)
            print(f"\nImplementation complete. Loops: {loop_count}. Correctness: {corr_score}/10. Succinctness: {succ_score}/10.")
            print(f"Files at: {WORKING_DIR}/implementer/")
            print(f"DONE: implementer delivered after {loop_count} loop(s), correctness {corr_score}/10, succinctness {succ_score}/10, status DONE, files at {WORKING_DIR}/implementer/")
            return

        if loop_count >= max_loops:
            gaps = extract_gaps_from_files(loop_count)
            write_final_summary(loop_count, max_loops, "PARTIAL", last_corr_score, last_succ_score,
                               f"Stopped after reaching max loops ({max_loops}). {loop_count - 1} fix attempt(s) made.",
                               [], gaps=gaps, skeptic=last_skeptic)
            print(f"\nDONE: implementer stopped after {max_loops} loops (cap), correctness {last_corr_score}/10, succinctness {last_succ_score}/10, status PARTIAL, gaps remain")
            print(f"Partial summary at: {WORKING_DIR}/outputs/summary.json")
            return

        # Both not done, spawn Fixer and loop
        why_needs_work = []
        if corr_verdict == "NEEDS_WORK":
            why_needs_work.append(f"Correctness review returned NEEDS_WORK ({corr_score}/10)")
        if succ_verdict == "NEEDS_WORK":
            why_needs_work.append(f"Succinctness review returned NEEDS_WORK ({succ_score}/10)")
        print(f"[{loop_count}] Reviewers found issues: {'; '.join(why_needs_work)} - spawning Fixer")

        spawn_fixer(task, loop_count)
        loop_count += 1
        print(f"[{loop_count}] Moving to next loop")


if __name__ == "__main__":
    task, max_loops = parse_args()
    run_loop(task, max_loops)
