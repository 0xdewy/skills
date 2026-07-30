#!/usr/bin/env python3
"""Run the repository-wide positive/negative skill-description routing matrix."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import run_evals


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "routing.json"
DEFAULT_RESULTS = Path("/tmp/routing-eval-results")
PROBE = """Routing probe only. Do not execute the request. Choose from installed
skills using their name and description. Reply with exactly one line:
ROUTE: <skill-name>
Use ROUTE: direct when no installed skill should handle it.

REQUEST:
{prompt}"""


def parse_route(output: str):
    matches = re.findall(r"^ROUTE:\s*([a-z0-9-]+)\s*$", output, re.I | re.M)
    return matches[-1].lower() if matches else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", default="auto", choices=["auto", *run_evals.BACKENDS])
    ap.add_argument("--model", default=run_evals.DEFAULT_MODEL,
                    help="Backend model (default: backend/CLI configured model).")
    ap.add_argument("--skill", help="Run only one target skill's two cases.")
    ap.add_argument("--polarity", choices=["positive", "negative"])
    ap.add_argument("--results", default=str(DEFAULT_RESULTS))
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cases = json.loads(CASES.read_text())["evals"]
    if args.skill:
        cases = [case for case in cases if case["skill_name"] == args.skill]
    if args.polarity:
        cases = [case for case in cases if case["polarity"] == args.polarity]
    if not cases:
        sys.exit("No routing cases selected.")
    backend = run_evals.resolve_backend(args.backend)
    if args.dry_run:
        print(
            f"DRY RUN: {len(cases)} routing cases, backend={backend}, "
            f"model={args.model or '(backend default)'}"
        )
        for case in cases:
            print(f"  {case['skill_name']:<22} {case['polarity']}: {case['prompt']}")
        return
    if backend is None:
        sys.exit(f"No available backend for {args.backend!r}.")

    results = Path(args.results) / backend
    rows = []
    for index, case in enumerate(cases, start=1):
        slug = f"{case['skill_name']}-{case['polarity']}"
        eval_dir = results / slug
        if eval_dir.exists():
            eval_dir.rename(eval_dir.with_name(f"{slug}.prev-{time.time_ns()}"))
        eval_dir.mkdir(parents=True)
        ev = {
            "id": slug,
            "prompt_type": "activation",
            "prompt": PROBE.format(prompt=case["prompt"]),
        }
        run = run_evals.run_eval(
            backend, ev, case["skill_name"], eval_dir, args.model, args.timeout
        )
        output = (eval_dir / "output.txt").read_text() if (eval_dir / "output.txt").exists() else ""
        route = parse_route(output)
        passed = (
            route == case["skill_name"] if case["polarity"] == "positive"
            else route != case["skill_name"] and route is not None
        )
        row = {**case, "route": route, "passed": passed, "run": run}
        rows.append(row)
        print(
            f"[{index:02}/{len(cases)}] {slug:<34} route={route or 'INVALID':<22} "
            f"{'PASS' if passed else 'FAIL'}"
        )

    summary = {
        "backend": backend,
        "model": args.model,
        "passed": sum(row["passed"] for row in rows),
        "total": len(rows),
        "usage": {
            key: sum(row["run"].get("usage", {}).get(key, 0) for row in rows)
            for key in sorted({k for row in rows for k in row["run"].get("usage", {})})
        },
        "results": rows,
    }
    results.mkdir(parents=True, exist_ok=True)
    (results / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\n{summary['passed']}/{summary['total']} passed; wrote {results / 'summary.json'}")
    raise SystemExit(0 if summary["passed"] == summary["total"] else 1)


if __name__ == "__main__":
    main()
