#!/usr/bin/env python3
"""
LLM-as-judge grader template for skills whose output is free-form text or
workflow behavior, where deterministic substring checks are too weak.

Usage:
    python3 llm_judge_grade.py --results /tmp/<skill>-run [--evals evals/evals.json] [--model claude-sonnet-4-5]

For each eval case, the grader gathers the recorded run artifacts under
<results>/eval-<id>/ (or <results>/ if flat), sends them to an LLM judge with a
rubric (accuracy / completeness / process / efficiency), and parses a strict
JSON verdict. Deterministic fields on the eval (required_regex, forbidden_regex,
required_files) are also checked and folded into the final pass/fail. Results
are written to <results>/grading.json.

Adapt the rubric wording, the artifact-gathering, and the model choice to the
skill you are grading. Anthropic's multi-agent team found a single LLM judge
with one rubric prompt aligns best with human judgment.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RUBRIC = """You are grading the output of an AI skill on a single test case.

TASK PROMPT (what the skill was asked to do):
{prompt}

EXPECTED OUTPUT (the target behavior, prose):
{expected}

ACCEPTANCE ASSERTIONS (each must hold):
{expectations}

ACTUAL RUN ARTIFACTS (what the skill produced):
{artifacts}

Grade the run against this rubric. Each criterion is scored 0.0 to 1.0:
- accuracy: claims/code match reality; no hallucination
- completeness: every requested part is present
- process: followed the intended workflow (e.g. spawned/avoided agents appropriately, used the right path)
- efficiency: no gross waste (over-spawning, needless churn)

Then output STRICT JSON only (no prose, no markdown fences) in exactly this shape:
{{
  "score": <overall 0.0-1.0, weighted toward accuracy and completeness>,
  "pass": <true if score >= 0.7 AND every acceptance assertion holds, else false>,
  "criteria": {{"accuracy": <0-1>, "completeness": <0-1>, "process": <0-1>, "efficiency": <0-1>}},
  "assertions_held": [<list which of the acceptance assertions held, by short name>],
  "evidence": "<one or two sentences citing concrete evidence from the artifacts>",
  "issues": ["<short, specific failure>", "..."]
}}
"""


def load_evals(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        return data.get("skill_name", Path(path).parts[-3]), data.get("evals", [])
    return Path(path).parts[-3], data


def gather_artifacts(results_dir, eval_id):
    candidates = [results_dir / f"eval-{eval_id}", results_dir]
    out = []
    for base in candidates:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in {".md", ".json", ".txt", ".py", ".sh", ".log", ".ts", ".js"}:
                try:
                    body = p.read_text(errors="replace")
                except Exception:
                    continue
                if len(body) > 20000:
                    body = body[:20000] + "\n...[truncated]"
                out.append(f"--- {p.relative_to(results_dir)} ---\n{body}")
        if out:
            break
    return "\n\n".join(out) if out else "(no artifacts found)"


def call_judge(prompt, model):
    try:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    except Exception as e:
        sys.stderr.write(f"  (anthropic SDK unavailable: {e}; falling back to claude CLI)\n")
    try:
        res = subprocess.run(
            ["claude", "--print", "--model", model, prompt],
            capture_output=True, text=True, timeout=180,
        )
        if res.returncode != 0:
            sys.stderr.write(f"  (claude CLI failed: {res.stderr.strip()})\n")
            return ""
        return res.stdout
    except Exception as e:
        sys.stderr.write(f"  (claude CLI unavailable: {e})\n")
        return ""


def extract_json(text):
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def deterministic_checks(eval_obj, artifacts_text):
    held, failed = [], []
    for rx in eval_obj.get("required_regex", []) or []:
        (held if re.search(rx, artifacts_text) else failed).append(f"required_regex {rx!r}")
    for rx in eval_obj.get("forbidden_regex", []) or []:
        (held if not re.search(rx, artifacts_text) else failed).append(f"forbidden_regex {rx!r}")
    return held, failed


def grade_eval(eval_obj, results_dir, model):
    eid = eval_obj.get("id", "?")
    artifacts_text = gather_artifacts(results_dir, eid)
    prompt = RUBRIC.format(
        prompt=eval_obj.get("prompt", ""),
        expected=eval_obj.get("expected_output", ""),
        expectations="\n".join(f"- {e}" for e in eval_obj.get("expectations", []) or []) or "- (none listed)",
        artifacts=artifacts_text,
    )
    raw = call_judge(prompt, model)
    verdict = extract_json(raw) or {
        "score": 0.0, "pass": False, "criteria": {}, "evidence": "", "issues": [],
        "judge_error": "no parseable JSON returned",
    }
    det_held, det_failed = deterministic_checks(eval_obj, artifacts_text)
    if det_failed:
        verdict["pass"] = False
        verdict.setdefault("issues", []).append("Failed deterministic checks: " + ", ".join(det_failed))
    verdict["deterministic_held"] = det_held
    verdict["eval_id"] = eid
    verdict["anti_trigger"] = eval_obj.get("prompt_type") == "anti_trigger"
    return verdict


def main():
    ap = argparse.ArgumentParser(description="LLM-as-judge grader for skill evals.")
    ap.add_argument("--results", required=True, help="Run artifacts root dir.")
    ap.add_argument("--evals", default="evals/evals.json", help="Path to evals.json.")
    ap.add_argument("--model", default=os.environ.get("GRADE_MODEL", "claude-sonnet-4-5"))
    args = ap.parse_args()

    results_dir = Path(args.results)
    skill_name, evals = load_evals(args.evals)
    if not evals:
        sys.exit("No evals found.")

    details = []
    for ev in evals:
        print(f"Grading eval {ev.get('id', '?')}...")
        details.append(grade_eval(ev, results_dir, args.model))

    passed = sum(1 for d in details if d.get("pass"))
    summary = {
        "skill_name": skill_name,
        "model": args.model,
        "summary": {
            "passed": passed,
            "failed": len(details) - passed,
            "total": len(details),
            "pass_rate": round(passed / len(details), 3) if details else 0.0,
        },
        "details": details,
    }
    out_path = results_dir / "grading.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {out_path} — {passed}/{len(details)} passed (pass rate {summary['summary']['pass_rate']})")
    sys.exit(0 if passed == len(details) else 1)


if __name__ == "__main__":
    main()
