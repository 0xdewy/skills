#!/usr/bin/env python3
"""Compare a forced skill run with a direct-work baseline on outcome criteria.

Only evals with ``outcome_expectations`` are eligible. Workflow expectations
are deliberately excluded so the skill is measured by task quality and cost,
not by whether it followed its own instructions.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from pathlib import Path

import run_evals


DIRECT_PREFIX = (
    "Solve this task directly. Do not invoke or load any repository skill. "
    "Optimize for the requested outcome and verify the result.\n\n"
)


def eligible_evals(skill: str, ids: set[int]) -> list[dict]:
    path = run_evals.SKILLS / skill / "evals" / "evals.json"
    if not path.is_file():
        raise ValueError(f"no evals.json found for skill {skill!r}")
    selected = []
    for ev in run_evals.load_evals(path):
        if ids and ev.get("id") not in ids:
            continue
        if ev.get("outcome_expectations"):
            selected.append(ev)
    if not selected:
        qualifier = f" for ids {sorted(ids)}" if ids else ""
        raise ValueError(f"no ablation-ready evals{qualifier}; add outcome_expectations")
    return selected


def arm_eval(ev: dict, arm: str) -> dict:
    candidate = copy.deepcopy(ev)
    candidate["prompt_type"] = "forced" if arm == "skill" else "activation"
    if arm == "direct":
        candidate["prompt"] = DIRECT_PREFIX + candidate["prompt"]
    candidate["expectations"] = candidate.pop("outcome_expectations")
    candidate["expected_output"] = candidate.pop(
        "outcome_expected", candidate.get("expected_output", "")
    )
    for field in ("required_regex", "forbidden_regex", "required_files", "manual_checks"):
        candidate.pop(field, None)
    return candidate


def verdict(summary: dict | None) -> dict:
    if not summary:
        return {"pass": False, "score": 0.0, "judge_error": "no grading result"}
    details = summary.get("details") or []
    return details[0] if details else {
        "pass": False, "score": 0.0, "judge_error": "grading result has no details"
    }


def usage_total(run: dict, backend: str) -> int:
    usage = run.get("usage", {})
    if isinstance(usage.get("total_tokens"), (int, float)):
        return usage["total_tokens"]
    if backend == "claude":
        return sum(
            usage.get(key, 0) for key in (
                "input_tokens", "cache_creation_input_tokens",
                "cache_read_input_tokens", "output_tokens",
            )
            if isinstance(usage.get(key, 0), (int, float))
        )
    return sum(
        usage.get(key, 0) for key in ("input_tokens", "output_tokens")
        if isinstance(usage.get(key, 0), (int, float))
    )


def run_arm(backend: str, skill: str, ev: dict, arm: str, case_dir: Path,
            model: str | None, grader_model: str, timeout: int) -> dict:
    arm_dir = case_dir / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    candidate = arm_eval(ev, arm)
    result = run_evals.run_eval(backend, candidate, skill, arm_dir / f"eval-{ev['id']}", model, timeout)
    if result["status"] not in run_evals.RAN_STATUSES:
        return {"arm": arm, "run": result, "pass": False, "score": 0.0}

    evals_path = arm_dir / "evals.json"
    evals_path.write_text(json.dumps({"skill_name": f"{skill}-{arm}", "evals": [candidate]}, indent=2))
    summary, grader, error = run_evals.grade_skill(
        skill, arm_dir, evals_path, grader_model, "generic"
    )
    judged = verdict(summary)
    return {
        "arm": arm,
        "run": result,
        "pass": bool(judged.get("pass")),
        "score": float(judged.get("score", 0.0)),
        "usage_total": usage_total(result, backend),
        "grader": grader,
        "grader_error": error,
        "verdict": judged,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run skill-vs-direct outcome ablations.")
    ap.add_argument("--skill", required=True)
    ap.add_argument("--id", help="comma/space-separated eval ids")
    ap.add_argument("--backend", default="auto", choices=["auto", "claude", "codex", "opencode"])
    ap.add_argument("--model", default=run_evals.DEFAULT_MODEL)
    ap.add_argument("--grader-model", default=run_evals.DEFAULT_GRADER_MODEL)
    ap.add_argument("--results", default="/tmp/skill-ablation")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ids = {int(part) for part in re.split(r"[,\s]+", args.id) if part} if args.id else set()
    try:
        evals = eligible_evals(args.skill, ids)
    except ValueError as exc:
        ap.error(str(exc))

    backend = run_evals.resolve_backend(args.backend)
    if args.dry_run:
        print(f"DRY RUN: {args.skill}, {len(evals)} case(s), backend={backend or '(none)'}")
        for ev in evals:
            print(f"  eval-{ev['id']}: skill vs direct; {len(ev['outcome_expectations'])} outcome criteria")
        return 0
    if backend is None:
        ap.error(f"no available backend for {args.backend!r}")

    root = Path(args.results) / args.skill / str(time.time_ns())
    cases = []
    for ev in evals:
        case_dir = root / f"eval-{ev['id']}"
        skill_result = run_arm(
            backend, args.skill, ev, "skill", case_dir, args.model,
            args.grader_model, args.timeout,
        )
        direct_result = run_arm(
            backend, args.skill, ev, "direct", case_dir, args.model,
            args.grader_model, args.timeout,
        )
        cases.append({
            "eval_id": ev["id"],
            "skill": skill_result,
            "direct": direct_result,
            "score_uplift": round(skill_result["score"] - direct_result["score"], 3),
            "usage_delta": skill_result.get("usage_total", 0) - direct_result.get("usage_total", 0),
        })
        print(
            f"eval-{ev['id']}: score {skill_result['score']:.2f} vs "
            f"{direct_result['score']:.2f}; usage delta "
            f"{cases[-1]['usage_delta']:+g}"
        )

    summary = {
        "skill": args.skill,
        "backend": backend,
        "model": args.model,
        "grader_model": args.grader_model,
        "cases": cases,
        "mean_score_uplift": round(sum(case["score_uplift"] for case in cases) / len(cases), 3),
        "total_usage_delta": sum(case["usage_delta"] for case in cases),
        "note": "Direct-arm routing is prompt-controlled; inspect run artifacts if the backend ignored it.",
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote {root / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
