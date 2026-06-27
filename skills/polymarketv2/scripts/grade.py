#!/usr/bin/env python3
"""Grade agent answers for the polymarketv2 skill against evals/evals.json.

Each eval case has:
  - id, prompt
  - required:  list of substrings/regexes that MUST appear (case-insensitive)
  - forbidden: list of substrings/regexes that must NOT appear

`required`/`forbidden` entries are either:
  - a plain string (case-insensitive substring match), or
  - an object {"regex": "..."} (case-insensitive regex search).

Forbidden matching uses regex word boundaries where given, so e.g.
`\\bpy-clob-client\\b(?!-v2)` does NOT false-fail on the valid `py-clob-client-v2`.

Answers come from a JSON file mapping eval id -> agent response string:
    { "1": "...answer text...", "2": "..." }

Usage:
    python scripts/grade.py --answers answers.json --out grading.json
    python scripts/grade.py --answers answers.json          # prints summary, no file
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent.parent / "evals" / "evals.json"


def matches(answer: str, rule) -> bool:
    """True if `rule` matches `answer` (case-insensitive)."""
    if isinstance(rule, dict) and "regex" in rule:
        return re.search(rule["regex"], answer, re.IGNORECASE) is not None
    return str(rule).lower() in answer.lower()


def grade_case(case: dict, answer: str) -> dict:
    missing = [r for r in case.get("required", []) if not matches(answer, r)]
    present_forbidden = [f for f in case.get("forbidden", []) if matches(answer, f)]
    ok = not missing and not present_forbidden
    return {
        "id": case["id"],
        "ok": ok,
        "missing_required": missing,
        "present_forbidden": present_forbidden,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Grade polymarketv2 skill answers.")
    ap.add_argument("--answers", required=True, help="JSON mapping eval id -> answer text")
    ap.add_argument("--out", help="write grading.json here (optional)")
    args = ap.parse_args()

    cases = json.loads(EVALS.read_text())
    answers = json.loads(Path(args.answers).read_text())
    # normalize keys to strings
    answers = {str(k): v for k, v in answers.items()}

    results = []
    for case in cases:
        ans = answers.get(str(case["id"]))
        if ans is None:
            results.append(
                {"id": case["id"], "ok": False, "missing_required": ["<no answer provided>"],
                 "present_forbidden": []}
            )
            continue
        results.append(grade_case(case, ans))

    passed = sum(1 for r in results if r["ok"])
    summary = {
        "total": len(cases),
        "passed": passed,
        "failed": len(cases) - passed,
        "results": results,
    }

    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2))

    print(f"{passed}/{len(cases)} cases passed")
    for r in results:
        if not r["ok"]:
            why = []
            if r["missing_required"]:
                why.append(f"missing {r['missing_required']}")
            if r["present_forbidden"]:
                why.append(f"forbidden {r['present_forbidden']}")
            print(f"  FAIL #{r['id']}: {'; '.join(why)}")

    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
