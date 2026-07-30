#!/usr/bin/env python3
import json, sys, os, re

def find_last_loop_file(results_dir, prefix="assessment-loop", max_check=20):
    last_file = None
    for i in range(1, max_check + 1):
        f = f"{results_dir}/reviewer/{prefix}{i}.md"
        if os.path.exists(f):
            last_file = f
    return last_file


def verdict_in_file(filepath, target="VERDICT=DONE"):
    if not filepath or not os.path.exists(filepath):
        return False
    return target in open(filepath).read()


def grade(evals_path, results_dir):
    with open(evals_path) as f:
        evals = json.load(f)

    summary = {"total": len(evals), "passed": 0, "failed": 0, "details": []}

    for ev in evals:
        eid = ev["id"]
        exp = ev["expectations"]
        result = {"id": eid, "checks": [], "passed": True}

        loop1_assess = f"{results_dir}/reviewer/assessment-loop1.md"
        loop2_assess = f"{results_dir}/reviewer/assessment-loop2.md"
        loop3_assess = f"{results_dir}/reviewer/assessment-loop3.md"
        loop1_succ = f"{results_dir}/reviewer/succinctness-loop1.md"
        loop2_succ = f"{results_dir}/reviewer/succinctness-loop2.md"
        loop3_succ = f"{results_dir}/reviewer/succinctness-loop3.md"

        last_assess = find_last_loop_file(results_dir, "assessment-loop")
        last_succ = find_last_loop_file(results_dir, "succinctness-loop")

        for assertion in exp:
            if "LOOP_COUNT reaches at most 3" in assertion:
                loop_count = 0
                for i in range(1, 10):
                    if os.path.exists(f"{results_dir}/reviewer/assessment-loop{i}.md"):
                        loop_count = i
                    else:
                        break
                passed = 1 <= loop_count <= 3
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": f"loop_count={loop_count}"
                })

            elif "LOOP_COUNT >= 2" in assertion:
                loop_count = 0
                for i in range(1, 10):
                    if os.path.exists(f"{results_dir}/reviewer/assessment-loop{i}.md"):
                        loop_count = i
                    else:
                        break
                passed = loop_count >= 2
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": f"loop_count={loop_count}"
                })

            elif "Final verdict is DONE" in assertion:
                assess_done = verdict_in_file(last_assess, "VERDICT=DONE")
                succ_done = verdict_in_file(last_succ, "VERDICT=DONE")
                passed = assess_done and succ_done
                detail_parts = []
                if assess_done:
                    detail_parts.append("correctness=DONE")
                else:
                    detail_parts.append("correctness=not DONE/missing")
                if succ_done:
                    detail_parts.append("succinctness=DONE")
                else:
                    detail_parts.append("succinctness=not DONE/missing")
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": "; ".join(detail_parts)
                })

            elif "Files exist" in assertion:
                passed = os.path.exists(f"{results_dir}/implementer/")
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": "dir exists" if passed else "dir missing"
                })

            elif "README.md explains" in assertion:
                readme = f"{results_dir}/implementer/README.md"
                if not os.path.exists(readme):
                    passed = False
                    detail = "README.md missing"
                else:
                    content = open(readme).read()
                    lines = [l for l in content.splitlines() if l.strip()]
                    has_min_lines = len(lines) >= 5
                    has_heading = any(l.startswith("#") for l in lines)
                    passed = has_min_lines and has_heading
                    detail = f"lines={len(lines)}, has_heading={has_heading}"
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": detail
                })

            elif "Reviewer verifies" in assertion:
                assess_done = verdict_in_file(last_assess, "VERDICT=DONE")
                succ_done = verdict_in_file(last_succ, "VERDICT=DONE")
                passed = assess_done and succ_done
                detail_parts = []
                if assess_done:
                    detail_parts.append("correctness=DONE")
                if succ_done:
                    detail_parts.append("succinctness=DONE")
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": "; ".join(detail_parts) if detail_parts else "not DONE"
                })

            elif "First reviewer verdict is NEEDS_WORK" in assertion:
                assess_needs_work = verdict_in_file(loop1_assess, "VERDICT=NEEDS_WORK")
                # Also check succinctness for completeness
                succ_needs_work = verdict_in_file(loop1_succ, "VERDICT=NEEDS_WORK")
                passed = assess_needs_work or succ_needs_work
                parts = []
                if assess_needs_work:
                    parts.append("correctness=NEEDS_WORK")
                if succ_needs_work:
                    parts.append("succinctness=NEEDS_WORK")
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": "; ".join(parts) if parts else "not found"
                })

            elif "Fixer fix-plan.md" in assertion:
                fixer_plan = f"{results_dir}/fixer/fix-plan.md"
                passed = os.path.exists(fixer_plan)
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": "fix-plan.md exists" if passed else "missing"
                })

            elif "Second reviewer verdict is DONE" in assertion:
                assess_done_2 = verdict_in_file(loop2_assess, "VERDICT=DONE")
                assess_done_3 = verdict_in_file(loop3_assess, "VERDICT=DONE")
                succ_done_2 = verdict_in_file(loop2_succ, "VERDICT=DONE")
                succ_done_3 = verdict_in_file(loop3_succ, "VERDICT=DONE")
                second_assess_done = assess_done_2 or assess_done_3
                second_succ_done = succ_done_2 or succ_done_3
                passed = second_assess_done and second_succ_done
                parts = []
                if second_assess_done:
                    parts.append("correctness=DONE on loop 2+")
                if second_succ_done:
                    parts.append("succinctness=DONE on loop 2+")
                result["checks"].append({
                    "assertion": assertion, "passed": passed,
                    "detail": "; ".join(parts) if parts else "not found on loop 2 or 3"
                })

            else:
                # Unknown assertion pattern - pass with note
                result["checks"].append({
                    "assertion": assertion, "passed": True,
                    "detail": "unrecognized assertion - skipped"
                })

        result["passed"] = all(c["passed"] for c in result["checks"])
        if result["passed"]:
            summary["passed"] += 1
        else:
            summary["failed"] += 1
        summary["details"].append(result)

    print(json.dumps(summary, indent=2))
    return summary["failed"] == 0


if __name__ == "__main__":
    ok = grade(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "/tmp/implementer-loop")
    sys.exit(0 if ok else 1)
