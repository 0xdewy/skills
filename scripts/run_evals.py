#!/usr/bin/env python3
"""
Eval runner: execute a skill's evals.json prompts against an agent backend,
capture artifacts into results/<skill>/eval-<id>/, then grade with the existing
per-skill grader (skills/<name>/evals/grade.py) or the canonical generic grader
(skills/skill-lab/scripts/llm_judge_grade.py).

Two phases per skill: RUN (invoke backend per eval) -> GRADE (one grader pass
over the skill's results dir, since graders iterate evals themselves).

Usage:
  python3 scripts/run_evals.py --skill goal                 # run goal's evals
  python3 scripts/run_evals.py --skill goal --id 1,3        # eval subset
  python3 scripts/run_evals.py --skill goal --limit 2       # first N evals
  python3 scripts/run_evals.py --all --dry-run              # plan only, invoke nothing
  python3 scripts/run_evals.py --skill goal --backend codex # pick backend
  python3 scripts/run_evals.py --skill goal --grader none   # run, skip grading

Backends (auto picks first available, preferring claude):
  claude   claude --print --model <m> "<prompt>"
  codex    codex exec -m <m> "<prompt>"
  opencode opencode run -m <m> "<prompt>"

Behavior evals force-load the target skill. ``activation`` and ``anti_trigger``
evals send the prompt raw, testing positive and negative routing respectively.
Backend failures mark an eval ERROR (not FAIL) so a flaky CLI never looks like a
skill regression. Grader regex checks always run; LLM-judge needs a key/CLI auth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CANONICAL_GRADER = SKILLS / "skill-lab" / "scripts" / "llm_judge_grade.py"
DEFAULT_RESULTS = Path("/tmp/eval-results")
DEFAULT_MODEL = os.environ.get("EVAL_MODEL")
DEFAULT_GRADER_MODEL = os.environ.get("GRADE_MODEL", "claude-sonnet-4-5")
PREFERENCE = ["claude", "codex", "opencode"]
PROMPT_TYPES = ("forced", "activation", "anti_trigger")

# Ran = produced output/artifacts (even if the CLI exited nonzero). Only
# timeout / missing-binary / exception count as not-ran (ERROR).
RAN_STATUSES = {"ok", "backend_nonzero"}


# ── backends ──────────────────────────────────────────────────────────────────

def _force_prefix(skill_name: str) -> str:
    skill_path = SKILLS / skill_name / "SKILL.md"
    return (
        f"Read and follow the skill at `{skill_path}`, then "
        f"complete this task:\n\n"
    )


def _claude_cmd(prompt, skill_name, force, model):
    cmd = ["claude", "--print", "--output-format", "json", "--no-session-persistence"]
    if model:
        cmd.extend(["--model", model])
    return [*cmd, (_force_prefix(skill_name) if force else "") + prompt]


def _codex_cmd(prompt, skill_name, force, model):
    cmd = [
        "codex", "exec", "--ephemeral", "--json", "--skip-git-repo-check",
        "--sandbox", "workspace-write",
    ]
    if model:
        cmd.extend(["-m", model])
    return [*cmd, (_force_prefix(skill_name) if force else "") + prompt]


def _opencode_cmd(prompt, skill_name, force, model):
    cmd = ["opencode", "run"]
    if model:
        cmd.extend(["-m", model])
    return [*cmd, (_force_prefix(skill_name) if force else "") + prompt]


BACKENDS = {
    "claude": {"bin": "claude", "build": _claude_cmd},
    "codex": {"bin": "codex", "build": _codex_cmd},
    "opencode": {"bin": "opencode", "build": _opencode_cmd},
}


def resolve_backend(name: str):
    if name == "auto":
        for n in PREFERENCE:
            if shutil.which(BACKENDS[n]["bin"]):
                return n
        return None
    if name in BACKENDS and shutil.which(BACKENDS[name]["bin"]):
        return name
    return None


# ── eval loading ──────────────────────────────────────────────────────────────

def load_evals(evals_path: Path):
    data = json.loads(evals_path.read_text())
    if isinstance(data, dict):
        return data.get("evals", [])
    return data


def discover_skills():
    out = []
    for d in sorted(SKILLS.iterdir()):
        if (d / "evals" / "evals.json").is_file():
            out.append(d.name)
    return out


def prompt_type(ev):
    return ev.get("prompt_type", "forced")


def materialize_fixtures(ev, workspace: Path):
    """Create an eval's declarative fixture and return initial content hashes.

    ``fixture_files`` maps relative POSIX paths to text. A null value creates a
    directory. Paths may not be absolute or escape the workspace.
    """
    fixtures = ev.get("fixture_files", {}) or {}
    if not isinstance(fixtures, dict):
        raise ValueError("fixture_files must be an object mapping paths to text or null")
    root = workspace.resolve()
    manifest = {}
    for raw_path, body in fixtures.items():
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError("fixture paths must be non-empty strings")
        rel = Path(raw_path)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"unsafe fixture path: {raw_path!r}")
        target = (workspace / rel).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"fixture path escapes workspace: {raw_path!r}")
        if body is None:
            target.mkdir(parents=True, exist_ok=True)
            manifest[raw_path] = None
            continue
        if not isinstance(body, str):
            raise ValueError(f"fixture content for {raw_path!r} must be text or null")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        manifest[raw_path] = hashlib.sha256(body.encode()).hexdigest()
    return manifest


def normalize_backend_output(backend: str, raw: str):
    """Return human output and exact usage reported by structured CLIs."""
    if backend == "claude":
        try:
            payload = json.loads(raw)
            usage = payload.get("usage") or {}
            return payload.get("result", ""), {
                key: value for key, value in usage.items()
                if isinstance(value, (int, float))
            }
        except (TypeError, ValueError):
            return raw, {}
    if backend == "codex":
        messages = []
        usage = {}
        for line in raw.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            item = event.get("item") or {}
            if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                messages.append(item.get("text", ""))
            if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                usage = {
                    key: value for key, value in event["usage"].items()
                    if isinstance(value, (int, float))
                }
        return "\n".join(filter(None, messages)) or raw, usage
    return raw, {}


def backend_reported_error(backend: str, raw: str):
    if backend == "claude":
        try:
            payload = json.loads(raw)
            return bool(payload.get("is_error")), payload.get("result", "")
        except (TypeError, ValueError):
            return False, ""
    if backend == "codex":
        errors = []
        for line in raw.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") in {"error", "turn.failed"}:
                message = event.get("message") or (event.get("error") or {}).get("message")
                if message:
                    errors.append(message)
        return bool(errors), errors[-1] if errors else ""
    return False, ""


# ── run phase ─────────────────────────────────────────────────────────────────

def run_eval(backend, ev, skill_name, eval_dir: Path, model, timeout):
    kind = prompt_type(ev)
    force = kind == "forced"
    prompt = ev.get("prompt", "")
    if ev.get("context"):
        prompt = (
            "EVALUATION CONTEXT (authoritative):\n"
            f"{ev['context']}\nA concrete fixture is present in the current working directory.\n\n"
            f"TASK:\n{prompt}"
        )
    cmd = BACKENDS[backend]["build"](prompt, skill_name, force, model)
    workspace = eval_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        fixture_manifest = materialize_fixtures(ev, workspace)
    except ValueError as exc:
        (eval_dir / "output.txt").write_text("")
        (eval_dir / "stderr.txt").write_text(str(exc))
        return {"status": "fixture_error", "detail": str(exc)}
    meta = {
        "eval_id": ev.get("id"),
        "backend": backend,
        "skill": skill_name,
        "prompt_type": kind,
        "force_skill": force,
        "fixture_manifest": fixture_manifest,
        "cmd": " ".join(shlex.quote(c) for c in cmd),
    }
    (eval_dir / "run.json").write_text(json.dumps(meta, indent=2))
    try:
        t0 = time.time()
        env = os.environ.copy()
        env.update({"WORKSPACE": str(workspace), "OUTPUT_DIR": str(workspace)})
        proc = subprocess.run(
            cmd, cwd=str(workspace), capture_output=True,
            text=True, timeout=timeout, env=env, stdin=subprocess.DEVNULL,
        )
        raw = proc.stdout or ""
        output, usage = normalize_backend_output(backend, raw)
        reported_error, error_detail = backend_reported_error(backend, raw)
        (eval_dir / "backend-output.jsonl").write_text(raw)
        (eval_dir / "output.txt").write_text(output)
        (eval_dir / "stderr.txt").write_text(proc.stderr or "")
        status = "backend_error" if reported_error else (
            "ok" if proc.returncode == 0 else "backend_nonzero"
        )
        result = {"status": status, "returncode": proc.returncode,
                  "elapsed": round(time.time() - t0, 1), "usage": usage}
        if error_detail:
            result["detail"] = error_detail
        meta["result"] = result
        (eval_dir / "run.json").write_text(json.dumps(meta, indent=2))
        return result
    except subprocess.TimeoutExpired:
        (eval_dir / "output.txt").write_text("(timeout)")
        return {"status": "timeout", "elapsed": timeout}
    except FileNotFoundError:
        return {"status": "backend_missing"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


# ── grade phase ───────────────────────────────────────────────────────────────

def _extract_json(text):
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


def _pick_grader(skill_name, mode):
    if mode == "generic":
        return CANONICAL_GRADER
    custom = SKILLS / skill_name / "evals" / "grade.py"
    return custom if custom.exists() else CANONICAL_GRADER


def grade_skill(skill_name, results_dir: Path, evals_path: Path, model, mode):
    """Run the chosen grader over results_dir. Graders come in two interfaces:
    flag-form (--results/--evals/--model; ego + canonical) and positional-form
    (evals results model; review loops), and emit either <results>/grading.json
    or JSON on stdout. Try flag then positional; accept either output form."""
    grader = _pick_grader(skill_name, mode)
    forms = [
        [sys.executable, str(grader), "--results", str(results_dir),
         "--evals", str(evals_path), "--model", model],
        [sys.executable, str(grader), str(evals_path), str(results_dir), model],
    ]
    last_stderr = ""
    for cmd in forms:
        grading_json = results_dir / "grading.json"
        grading_json.unlink(missing_ok=True)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        except subprocess.TimeoutExpired:
            last_stderr = "grader timeout"
            continue
        except Exception as exc:
            last_stderr = str(exc)
            continue
        last_stderr = (r.stderr or "").strip()[-400:]
        summary = None
        if grading_json.exists():
            try:
                summary = json.loads(grading_json.read_text())
            except Exception:
                summary = None
        if summary is None:
            summary = _extract_json(r.stdout)
        if summary is not None:
            return summary, grader.name, last_stderr
    return None, grader.name, last_stderr


def pass_total(summary):
    if not summary:
        return None, None
    if isinstance(summary.get("summary"), dict):
        s = summary["summary"]
        return s.get("passed"), s.get("total")
    return summary.get("passed"), summary.get("total")


# ── dry run ───────────────────────────────────────────────────────────────────

def dry_run(skills, ids, limit, selected_type, backend, model, results):
    print(f"DRY RUN — {len(skills)} skill(s), backend={backend or '(none available)'}, "
          f"model={model or '(backend default)'}, results={results}")
    print("(nothing will be invoked)\n")
    total = 0
    for sk in skills:
        evals = load_evals(SKILLS / sk / "evals" / "evals.json")
        if ids:
            evals = [e for e in evals if e.get("id") in ids]
        if selected_type != "all":
            evals = [e for e in evals if prompt_type(e) == selected_type]
        if limit:
            evals = evals[:limit]
        if not evals:
            continue
        grader = _pick_grader(sk, "auto")
        grader_rel = grader.relative_to(ROOT)
        print(f"{sk}  ({len(evals)} eval(s), grader={grader_rel})")
        for ev in evals:
            kind = prompt_type(ev)
            force = kind == "forced"
            tag = {"forced": "force", "activation": "route+", "anti_trigger": "route-"}[kind]
            eid = ev.get("id")
            if backend in BACKENDS:
                cmd = BACKENDS[backend]["build"](
                    ev.get("prompt", ""), sk, force, model)
                cmdstr = " ".join(shlex.quote(c) for c in cmd)
                if len(cmdstr) > 140:
                    cmdstr = cmdstr[:137] + "..."
            else:
                cmdstr = "(no backend available)"
            print(f"  [{tag}] eval-{eid}: {cmdstr}")
            total += 1
        print()
    print(f"{total} eval(s) planned.")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Run skill evals against an agent backend, then grade them.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--skill", help="Skill name to run (or omit with --all).")
    ap.add_argument("--all", action="store_true", help="Run every skill with an evals.json.")
    ap.add_argument("--backend", default="auto",
                    choices=["auto", "claude", "codex", "opencode"],
                    help="Agent backend (default: auto, prefer claude).")
    ap.add_argument("--id", help="Comma/space-separated eval ids to include.")
    ap.add_argument("--limit", type=int, help="Run only the first N evals per skill.")
    ap.add_argument("--prompt-type", default="all", choices=["all", *PROMPT_TYPES],
                    help="Filter behavior or routing evals (default: all).")
    ap.add_argument("--grader", default="auto", choices=["auto", "generic", "none"],
                    help="auto = per-skill grade.py if present else canonical; "
                         "generic = always canonical; none = skip grading.")
    ap.add_argument("--results", default=str(DEFAULT_RESULTS),
                    help=f"Results root (default: {DEFAULT_RESULTS}).")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="Backend model (default: backend/CLI configured model).")
    ap.add_argument("--grader-model", default=DEFAULT_GRADER_MODEL,
                    help=f"LLM judge model (default: {DEFAULT_GRADER_MODEL}).")
    ap.add_argument("--timeout", type=int, default=300,
                    help="Per-eval backend timeout in seconds (default: 300).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the plan and exit; invoke nothing.")
    args = ap.parse_args()

    if not args.skill and not args.all:
        ap.error("--skill <name> or --all is required")
    if args.skill and args.all:
        ap.error("use --skill or --all, not both")

    skills = discover_skills() if args.all else [args.skill]
    for sk in skills:
        if not (SKILLS / sk / "evals" / "evals.json").is_file():
            sys.exit(f"no evals.json found for skill '{sk}'")

    ids = {int(x) for x in re.split(r"[,\s]+", args.id) if x.strip()} if args.id else set()
    results = Path(args.results)

    # dry run needs no backend
    if args.dry_run:
        backend = resolve_backend(args.backend)
        if backend is None:
            backend = None
        dry_run(skills, ids, args.limit, args.prompt_type, backend, args.model, results)
        return

    backend = resolve_backend(args.backend)
    if backend is None:
        sys.exit(f"No available backend for '{args.backend}'. "
                 f"Install claude/codex/opencode, or pass --backend.")

    print(f"Backend: {backend}  Model: {args.model or '(backend default)'}  "
          f"Grader: {args.grader} ({args.grader_model})  Results: {results}\n")

    overall = []
    exit_nonzero = False
    for sk in skills:
        evals = load_evals(SKILLS / sk / "evals" / "evals.json")
        if ids:
            evals = [e for e in evals if e.get("id") in ids]
        if args.prompt_type != "all":
            evals = [e for e in evals if prompt_type(e) == args.prompt_type]
        if args.limit:
            evals = evals[:args.limit]
        if not evals:
            continue

        sk_dir = results / sk
        print(f"== {sk} ({len(evals)} evals) ==")
        runs = {}
        for ev in evals:
            eid = ev.get("id")
            edir = sk_dir / f"eval-{eid}"
            if edir.exists():
                archived = edir.with_name(f"{edir.name}.prev-{time.time_ns()}")
                edir.rename(archived)
            edir.mkdir(parents=True, exist_ok=True)
            run = run_eval(backend, ev, sk, edir, args.model, args.timeout)
            runs[eid] = run
            ran = "ok" if run["status"] in RAN_STATUSES else "ERROR"
            print(f"  eval-{eid}: run={ran} ({run['status']}"
                  f"{', ' + str(run.get('elapsed')) + 's' if 'elapsed' in run else ''})")

        # Write a filtered evals.json so the grader only scores evals that ran.
        filtered_path = sk_dir / "evals.json"
        filtered_path.write_text(json.dumps({"skill_name": sk, "evals": evals}, indent=2))

        if args.grader == "none":
            errors = sum(1 for r in runs.values() if r["status"] not in RAN_STATUSES)
            overall.append({"skill": sk, "passed": None, "total": len(evals),
                            "errored": errors, "grader": None,
                            "usage": {
                                key: sum(r.get("usage", {}).get(key, 0) for r in runs.values())
                                for key in sorted({k for r in runs.values() for k in r.get("usage", {})})
                            }})
            if errors:
                exit_nonzero = True
            print()
            continue

        summary, grader_name, err = grade_skill(
            sk, sk_dir, filtered_path, args.grader_model, args.grader)
        passed, total = pass_total(summary)
        if summary is None:
            print(f"  grader ({grader_name}) produced no parseable result: {err}")
            errored = sum(1 for r in runs.values() if r["status"] not in RAN_STATUSES)
            overall.append({"skill": sk, "passed": None, "total": len(evals),
                            "errored": errored, "grader": grader_name})
            exit_nonzero = True
        else:
            # Fold run-level errors: any eval that didn't run counts as errored.
            errored = sum(1 for r in runs.values() if r["status"] not in RAN_STATUSES)
            failed = (total - passed) if passed is not None and total is not None else None
            print(f"  graded: {passed}/{total} passed, {failed} failed"
                  f"{', ' + str(errored) + ' run-error(s)' if errored else ''}"
                  f"  (grader={grader_name})")
            overall.append({"skill": sk, "passed": passed, "total": total,
                            "errored": errored, "grader": grader_name,
                            "usage": {
                                key: sum(r.get("usage", {}).get(key, 0) for r in runs.values())
                                for key in sorted({k for r in runs.values() for k in r.get("usage", {})})
                            },
                            "summary": summary})
            if (passed is not None and total is not None and passed != total) or errored:
                exit_nonzero = True
        print()

    # overall table + summary.json
    print("=" * 60)
    print(f"{'skill':<22}{'passed':>10}{'total':>8}{'errors':>9}")
    print("-" * 60)
    for row in overall:
        p = "-" if row["passed"] is None else str(row["passed"])
        t = str(row["total"])
        e = str(row["errored"])
        print(f"{row['skill']:<22}{p:>10}{t:>8}{e:>9}")
    print("=" * 60)

    (results).mkdir(parents=True, exist_ok=True)
    (results / "summary.json").write_text(json.dumps(overall, indent=2))
    print(f"\nWrote {results / 'summary.json'}")

    sys.exit(1 if exit_nonzero else 0)


if __name__ == "__main__":
    main()
