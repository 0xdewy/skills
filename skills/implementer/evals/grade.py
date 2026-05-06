#!/usr/bin/env python3
import json, sys, os, re

def find_last_loop_file(results_dir, max_check=20):
    last_file = None
    for i in range(1, max_check + 1):
        f = f"{results_dir}/reviewer/assessment-loop{i}.md"
        if os.path.exists(f):
            last_file = f
    return last_file


def grade(evals_path, results_dir):
    with open(evals_path) as f:
        evals = json.load(f)

    summary = {"total": len(evals), "passed": 0, "failed": 0, "details": []}

    for ev in evals:
        eid = ev["id"]
        exp = ev["expectations"]
        result = {"id": eid, "checks": [], "passed": True}

        last_loop_file = find_last_loop_file(results_dir)
        loop1_file = f"{results_dir}/reviewer/assessment-loop1.md"

        for assertion in exp:
            if "LOOP_COUNT reaches at most 3" in assertion:
                loop_count = 0
                for i in range(1, 10):
                    if os.path.exists(f"{results_dir}/reviewer/assessment-loop{i}.md"):
                        loop_count = i
                    else:
                        break
                passed = 1 <= loop_count <= 3
                result["checks"].append({"assertion": assertion, "passed": passed, "detail": f"loop_count={loop_count}"})

            elif "Final verdict is DONE" in assertion:
                verdict_file = find_last_loop_file(results_dir)
                passed = verdict_file and "VERDICT=DONE" in open(verdict_file).read()
                result["checks"].append({"assertion": assertion, "passed": passed, "detail": "DONE found" if passed else "not found"})

            elif "Files exist" in assertion:
                passed = os.path.exists(f"{results_dir}/implementer/")
                result["checks"].append({"assertion": assertion, "passed": passed, "detail": "dir exists" if passed else "dir missing"})

            elif "README.md explains" in assertion:
                readme = f"{results_dir}/implementer/README.md"
                passed = os.path.exists(readme)
                result["checks"].append({"assertion": assertion, "passed": passed, "detail": "README exists" if passed else "missing"})

            elif "Reviewer verifies" in assertion:
                verdict_file = find_last_loop_file(results_dir)
                content = open(verdict_file).read() if verdict_file else ""
                passed = "VERDICT=DONE" in content
                result["checks"].append({"assertion": assertion, "passed": passed, "detail": "VERDICT=DONE" if passed else "not DONE"})

            elif "First reviewer verdict is NEEDS_WORK" in assertion:
                passed = os.path.exists(loop1_file) and "VERDICT=NEEDS_WORK" in open(loop1_file).read()
                result["checks"].append({"assertion": assertion, "passed": passed, "detail": "NEEDS_WORK found" if passed else "not found"})

            elif "Fixer fix-plan.md" in assertion:
                passed = os.path.exists(f"{results_dir}/fixer/fix-plan.md")
                result["checks"].append({"assertion": assertion, "passed": passed, "detail": "fix-plan.md exists" if passed else "missing"})

            elif "Second reviewer verdict is DONE" in assertion:
                loop2_file = f"{results_dir}/reviewer/assessment-loop2.md"
                loop3_file = f"{results_dir}/reviewer/assessment-loop3.md"
                second_done = (
                    (os.path.exists(loop2_file) and "VERDICT=DONE" in open(loop2_file).read()) or
                    (os.path.exists(loop3_file) and "VERDICT=DONE" in open(loop3_file).read())
                )
                passed = second_done
                result["checks"].append({"assertion": assertion, "passed": passed, "detail": "DONE found on loop 2 or 3" if passed else "not found"})

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