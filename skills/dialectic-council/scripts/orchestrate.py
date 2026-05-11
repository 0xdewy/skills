#!/usr/bin/env python3
"""
Dialectic Council orchestrator.

Phases:
  plan      — multi-model debate to produce a consensus implementation plan
  execute   — parallel implementation by all council members
  review    — cross-model flaw detection and majority-vote resolution
  synthesize — Claude merges the best implementation with validated fixes
  all       — run plan → execute → review → synthesize in sequence

Usage:
  python3 orchestrate.py --task "..." --phase all [--models claude,deepseek] [--output-dir .]
  python3 orchestrate.py --phase plan --session-dir /tmp/dialectic-council-abc123
"""

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from model_client import ModelClient, build_council


# ── Utilities ────────────────────────────────────────────────────────────────

def session_path(session_dir: Path, *parts: str) -> Path:
    p = session_dir.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def jdump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2))


def jload(path: Path):
    return json.loads(path.read_text())


def log(msg: str) -> None:
    print(msg, flush=True)


# ── Phase 1: Planning Debate ──────────────────────────────────────────────────

PLAN_PROPOSAL_SYSTEM = """You are a member of a multi-model AI council debating how to approach a task.
Produce a JSON object with exactly these keys:
  model       - your model name (string)
  approach    - one-sentence summary of your proposed approach (string)
  steps       - ordered list of implementation steps (array of strings)
  rationale   - why this approach is best (string)
  concerns    - concerns you have about ALTERNATIVE approaches, not your own (array of strings, may be empty)

Respond with ONLY the JSON object, no markdown fences, no extra text."""

PLAN_DISAGREE_SYSTEM = """You are reviewing rival implementation proposals from other AI council members.
You have seen all proposals. Now list your blocking disagreements — points where you believe
another proposal would lead to incorrect or significantly inferior output.

Respond with a JSON object:
  model          - your model name (string)
  round          - current debate round (integer)
  disagreements  - list of objects:
      target     - model name you disagree with (string)
      point      - specific objection (string)
      severity   - "blocking" or "minor" (string)

Respond with ONLY the JSON object. If you have no blocking disagreements, return an empty array for disagreements."""


async def phase_plan(council: list[ModelClient], task: str, session_dir: Path) -> dict:
    log("\n── Phase 1: Planning Debate ──────────────────────────────────────────")
    transcript = []
    round_num = 0
    max_rounds = 5

    while round_num < max_rounds:
        round_num += 1
        log(f"  Round {round_num}/{max_rounds}")

        if round_num == 1:
            prompt = f"TASK:\n{task}"
        else:
            prev_proposals = json.dumps(transcript[-len(council):], indent=2)
            prompt = (
                f"TASK:\n{task}\n\n"
                f"PREVIOUS PROPOSALS FROM OTHER COUNCIL MEMBERS:\n{prev_proposals}\n\n"
                "Revise your proposal to address the blocking concerns raised."
            )

        proposals = await asyncio.gather(
            *[_get_proposal(m, prompt, round_num) for m in council],
            return_exceptions=True,
        )

        valid_proposals = []
        for i, p in enumerate(proposals):
            if isinstance(p, Exception):
                log(f"    {council[i].name}: ERROR — {p}")
                continue
            valid_proposals.append(p)
            transcript.append(p)

        jdump(session_path(session_dir, "plan-debate.json"), transcript)

        proposals_text = json.dumps(valid_proposals, indent=2)
        disagree_prompt = (
            f"TASK:\n{task}\n\n"
            f"ALL PROPOSALS (round {round_num}):\n{proposals_text}"
        )

        disagrees = await asyncio.gather(
            *[_get_disagreements(m, disagree_prompt, round_num) for m in council],
            return_exceptions=True,
        )

        blocking_count = 0
        for d in disagrees:
            if isinstance(d, Exception):
                continue
            transcript.append(d)
            blocking_count += sum(
                1 for item in d.get("disagreements", [])
                if item.get("severity") == "blocking"
            )

        log(f"    Blocking disagreements: {blocking_count}")

        if blocking_count == 0:
            log(f"  Convergence reached at round {round_num}.")
            break

    consensus = _synthesize_plan(valid_proposals, task)
    jdump(session_path(session_dir, "consensus-plan.json"), consensus)
    log(f"  Consensus plan written to {session_dir}/consensus-plan.json")
    return consensus


async def _get_proposal(model: ModelClient, prompt: str, round_num: int) -> dict:
    raw = await model.call(prompt, system=PLAN_PROPOSAL_SYSTEM)
    data = _parse_json(raw, model.name)
    data["model"] = model.name
    data["round"] = round_num
    return data


async def _get_disagreements(model: ModelClient, prompt: str, round_num: int) -> dict:
    raw = await model.call(prompt, system=PLAN_DISAGREE_SYSTEM)
    data = _parse_json(raw, model.name)
    data["model"] = model.name
    data["round"] = round_num
    return data


def _synthesize_plan(proposals: list[dict], task: str) -> dict:
    all_steps = []
    for p in proposals:
        all_steps.extend(p.get("steps", []))
    deduped = list(dict.fromkeys(all_steps))
    return {
        "task": task,
        "steps": deduped,
        "contributing_models": [p.get("model") for p in proposals],
    }


# ── Phase 2: Parallel Execution ───────────────────────────────────────────────

EXECUTE_SYSTEM = """You are implementing a software task according to a consensus plan agreed upon by a council of AI models.
Produce a complete, working implementation. Write production-quality code.
After the implementation, end with exactly this line:
IMPLEMENTATION_DONE"""


async def phase_execute(council: list[ModelClient], session_dir: Path) -> dict:
    log("\n── Phase 2: Parallel Execution ────────────────────────────────────────")
    plan = jload(session_path(session_dir, "consensus-plan.json"))

    prompt = (
        f"TASK: {plan['task']}\n\n"
        f"CONSENSUS PLAN:\n{json.dumps(plan['steps'], indent=2)}\n\n"
        "Implement this plan completely."
    )

    results = await asyncio.gather(
        *[_execute_model(m, prompt, session_dir) for m in council],
        return_exceptions=True,
    )

    manifest = {}
    for i, result in enumerate(results):
        model_name = council[i].name
        if isinstance(result, Exception):
            log(f"    {model_name}: FAILED — {result}")
            manifest[model_name] = {"status": "failed", "error": str(result)}
        else:
            manifest[model_name] = {"status": "ok", "path": str(result)}
            log(f"    {model_name}: written to {result}")

    jdump(session_path(session_dir, "implementations-manifest.json"), manifest)
    return manifest


async def _execute_model(model: ModelClient, prompt: str, session_dir: Path) -> Path:
    output = await model.call(prompt, system=EXECUTE_SYSTEM)
    impl_dir = session_dir / model.name / "implementation"
    impl_dir.mkdir(parents=True, exist_ok=True)
    out_file = impl_dir / "output.md"
    out_file.write_text(output)
    return out_file


# ── Phase 3: Cross-Review Debate ─────────────────────────────────────────────

REVIEW_SYSTEM = """You are reviewing another AI model's implementation as part of a council review.
Identify concrete, specific flaws — bugs, logical errors, missing edge cases, security issues.
Style preferences are NOT flaws unless they cause incorrect behavior.

Respond with a JSON object:
  reviewer  - your model name (string)
  target    - the model you reviewed (string)
  flaws     - list of objects:
      id          - unique string like "flaw-001" (string)
      location    - where in the output the flaw appears (string)
      description - what is wrong (string)
      severity    - "critical", "major", or "minor" (string)
      fix         - concrete fix suggestion (string)

Respond with ONLY the JSON object. If you find no flaws, return an empty array for flaws."""

VOTE_SYSTEM = """You are voting on whether a reported flaw is real.
Respond with a JSON array of vote objects:
  flaw_id  - the flaw ID being voted on (string)
  voter    - your model name (string)
  verdict  - "REAL", "NITPICK", or "INVALID" (string)
  reason   - one-sentence justification (string)

Respond with ONLY the JSON array, no markdown fences."""


async def phase_review(council: list[ModelClient], session_dir: Path) -> dict:
    log("\n── Phase 3: Cross-Review Debate ───────────────────────────────────────")
    manifest = jload(session_path(session_dir, "implementations-manifest.json"))
    flaw_log: list[dict] = []
    round_num = 0
    max_rounds = 5

    implementations = {}
    for model_name, info in manifest.items():
        if info.get("status") == "ok":
            implementations[model_name] = Path(info["path"]).read_text()

    while round_num < max_rounds:
        round_num += 1
        log(f"  Round {round_num}/{max_rounds}")

        review_tasks = []
        pairs = []
        for reviewer in council:
            for target_name, impl_text in implementations.items():
                if reviewer.name == target_name:
                    continue
                pairs.append((reviewer, target_name))
                review_tasks.append(_review_impl(reviewer, target_name, impl_text))

        reviews = await asyncio.gather(*review_tasks, return_exceptions=True)

        all_flaws = []
        for (reviewer, target_name), result in zip(pairs, reviews):
            if isinstance(result, Exception):
                log(f"    {reviewer.name} → {target_name}: REVIEW ERROR — {result}")
                continue
            flaws = result.get("flaws", [])
            for flaw in flaws:
                flaw["reviewer"] = reviewer.name
                flaw["target"] = target_name
                flaw["round"] = round_num
                flaw["verdict"] = None
            all_flaws.extend(flaws)

        if not all_flaws:
            log("  No flaws reported. Consensus reached.")
            break

        log(f"  {len(all_flaws)} flaws reported, voting...")
        all_flaws = await _vote_on_flaws(council, all_flaws, implementations)
        flaw_log.extend(all_flaws)

        real_flaws = [f for f in all_flaws if f.get("verdict") == "REAL"]
        critical_real = [f for f in real_flaws if f.get("severity") == "critical"]
        log(f"    REAL: {len(real_flaws)}  (critical: {len(critical_real)})")

        if not critical_real and not [f for f in real_flaws if f.get("severity") == "major"]:
            log("  No critical/major REAL flaws. Consensus reached.")
            break

        # Apply fixes to implementations for next round
        implementations = await _apply_fixes(council, implementations, real_flaws, session_dir)

    jdump(session_path(session_dir, "flaw-log.json"), flaw_log)
    log(f"  Flaw log written to {session_dir}/flaw-log.json")
    return {"flaw_log": flaw_log, "final_implementations": implementations}


async def _review_impl(reviewer: ModelClient, target_name: str, impl_text: str) -> dict:
    prompt = (
        f"Review this implementation by model '{target_name}':\n\n"
        f"```\n{impl_text[:8000]}\n```"
    )
    raw = await reviewer.call(prompt, system=REVIEW_SYSTEM)
    data = _parse_json(raw, reviewer.name)
    data["reviewer"] = reviewer.name
    data["target"] = target_name
    return data


async def _vote_on_flaws(
    council: list[ModelClient],
    flaws: list[dict],
    implementations: dict,
) -> list[dict]:
    flaws_summary = json.dumps(
        [{"id": f["id"], "target": f["target"], "description": f["description"],
          "severity": f["severity"], "fix": f["fix"]} for f in flaws],
        indent=2,
    )

    vote_prompt = (
        f"Vote on each of these reported flaws.\n\n"
        f"FLAWS:\n{flaws_summary}"
    )

    all_votes: list[dict] = []
    vote_results = await asyncio.gather(
        *[_get_votes(m, vote_prompt) for m in council],
        return_exceptions=True,
    )
    for result in vote_results:
        if isinstance(result, Exception):
            continue
        if isinstance(result, list):
            all_votes.extend(result)

    majority = len(council) // 2 + 1
    for flaw in flaws:
        flaw_votes = [v for v in all_votes if v.get("flaw_id") == flaw["id"]]
        real_count = sum(1 for v in flaw_votes if v.get("verdict") == "REAL")
        if real_count >= majority:
            flaw["verdict"] = "REAL"
        else:
            flaw["verdict"] = "DISMISSED"
        flaw["votes"] = flaw_votes

    return flaws


async def _get_votes(model: ModelClient, prompt: str) -> list:
    raw = await model.call(prompt, system=VOTE_SYSTEM)
    return _parse_json(raw, model.name)


async def _apply_fixes(
    council: list[ModelClient],
    implementations: dict,
    real_flaws: list[dict],
    session_dir: Path,
) -> dict:
    """Ask each model to fix REAL flaws in its own implementation."""
    updated = dict(implementations)
    for model_member in council:
        my_flaws = [f for f in real_flaws if f.get("target") == model_member.name]
        if not my_flaws:
            continue
        fix_prompt = (
            f"Your implementation has these verified flaws that must be fixed:\n\n"
            f"{json.dumps(my_flaws, indent=2)}\n\n"
            f"Current implementation:\n```\n{implementations.get(model_member.name, '')[:8000]}\n```\n\n"
            "Produce the corrected implementation in full."
        )
        try:
            fixed = await model_member.call(fix_prompt)
            updated[model_member.name] = fixed
            fix_path = session_dir / model_member.name / "implementation" / "output-fixed.md"
            fix_path.parent.mkdir(parents=True, exist_ok=True)
            fix_path.write_text(fixed)
        except Exception as e:
            log(f"    {model_member.name}: fix application failed — {e}")
    return updated


# ── Phase 4: Synthesis ────────────────────────────────────────────────────────

SYNTHESIZE_SYSTEM = """You are the final synthesizer for a multi-model AI council.
You have received multiple independent implementations of the same task and a log of
verified flaws. Your job is to:
1. Pick the strongest base implementation
2. Apply all verified (REAL verdict) fixes from the flaw log
3. Produce the final, best-possible output

State which implementation you chose as the base and which patches you applied.
Then produce the final implementation."""


async def phase_synthesize(
    session_dir: Path,
    output_dir: Path,
    council: list[ModelClient],
) -> Path:
    log("\n── Phase 4: Synthesis ─────────────────────────────────────────────────")
    plan = jload(session_path(session_dir, "consensus-plan.json"))
    manifest = jload(session_path(session_dir, "implementations-manifest.json"))
    flaw_log_path = session_dir / "flaw-log.json"
    flaw_log = jload(flaw_log_path) if flaw_log_path.exists() else []

    real_flaws = [f for f in flaw_log if f.get("verdict") == "REAL"]

    impls_text = ""
    for model_name, info in manifest.items():
        if info.get("status") == "ok":
            content = Path(info["path"]).read_text()
            impls_text += f"\n\n=== {model_name} ===\n{content[:6000]}"

    synthesizer = next((m for m in council if m.name == "claude"), council[0])

    prompt = (
        f"TASK: {plan['task']}\n\n"
        f"IMPLEMENTATIONS:\n{impls_text}\n\n"
        f"VERIFIED FLAWS (must be fixed in final output):\n"
        f"{json.dumps(real_flaws, indent=2)[:4000]}"
    )

    final = await synthesizer.call(prompt, system=SYNTHESIZE_SYSTEM)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "dialectic-council-output.md"
    out_file.write_text(final)
    log(f"  Final output: {out_file}")
    return out_file


# ── Main ──────────────────────────────────────────────────────────────────────

def _parse_json(text: str, model_name: str):
    """Parse JSON from model output, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Return a safe fallback rather than crashing the whole pipeline
        return {"model": model_name, "parse_error": True, "raw": text[:500]}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Dialectic Council orchestrator")
    parser.add_argument("--task", help="Task description (required for --phase all or plan)")
    parser.add_argument(
        "--phase",
        choices=["plan", "execute", "review", "synthesize", "all"],
        default="all",
    )
    parser.add_argument("--session-dir", help="Existing session directory to resume")
    parser.add_argument("--output-dir", default=".", help="Where to write final output")
    parser.add_argument("--models", help="Comma-separated list of models (e.g. claude,deepseek)")
    args = parser.parse_args()

    requested = args.models.split(",") if args.models else None
    council = build_council(requested)

    if not council:
        print("ERROR: No models available. Run setup_keys.py to configure API keys.")
        sys.exit(1)

    log(f"Council: {', '.join(m.name for m in council)}")

    if args.session_dir:
        session_dir = Path(args.session_dir)
    else:
        session_id = str(uuid.uuid4())[:8]
        session_dir = Path(f"/tmp/dialectic-council-{session_id}")
        session_dir.mkdir(parents=True, exist_ok=True)

    log(f"Session: {session_dir}")
    output_dir = Path(args.output_dir)

    plan_rounds = 0
    review_rounds = 0

    if args.phase in ("plan", "all"):
        if not args.task:
            print("ERROR: --task is required for plan phase")
            sys.exit(1)
        plan = await phase_plan(council, args.task, session_dir)
        plan_rounds = plan.get("round_count", 1)

    if args.phase in ("execute", "all"):
        await phase_execute(council, session_dir)

    if args.phase in ("review", "all"):
        result = await phase_review(council, session_dir)
        review_rounds = result.get("rounds_completed", 1)

    if args.phase in ("synthesize", "all"):
        out = await phase_synthesize(session_dir, output_dir, council)
        print(f"\nDONE: dialectic-council — consensus reached in {plan_rounds} plan rounds, "
              f"{review_rounds} review rounds. Output: {out}")


if __name__ == "__main__":
    asyncio.run(main())
