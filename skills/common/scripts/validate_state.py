#!/usr/bin/env python3
"""Validate a goal run's durable status.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


GOAL_STATES = {"pending", "in_progress", "passed", "partial", "blocked"}
CRITERION_STATES = {"pending", "passed", "failed", "blocked"}

GOAL_TEMPLATE = {
    "schema_version": 1,
    "goal": "make verifier pass",
    "mode": "standard",
    "state": "in_progress",
    "cap": 8,
    "gate_type": "command",
    "current_iteration": 1,
    "attempts": 1,
    "criteria": [
        {"id": "verify", "state": "failed", "evidence": "iteration 1 output"}
    ],
    "last_evidence": "iteration 1 output",
    "blockers": [],
    "next_action": "diagnose verifier failure",
}

def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_common(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["state root must be an object"]
    if data.get("schema_version") != 1:
        return ["schema_version must equal 1"]
    return []


def validate_goal(data: Any) -> list[str]:
    errors = validate_common(data)
    if errors or not isinstance(data, dict):
        return errors
    if not nonempty(data.get("goal")):
        errors.append("goal must be non-empty")
    if data.get("mode") not in {"quick", "standard", "thorough"}:
        errors.append("mode must be quick, standard, or thorough")
    state = data.get("state")
    if state not in GOAL_STATES:
        errors.append(f"state must be one of {sorted(GOAL_STATES)}")
    if data.get("gate_type") not in {"command", "observable", "review", "mixed"}:
        errors.append("gate_type must be command, observable, review, or mixed")
    cap = data.get("cap")
    iteration = data.get("current_iteration")
    attempts = data.get("attempts")
    if not nonnegative_int(cap) or cap < 1:
        errors.append("cap must be a positive integer")
    if not nonnegative_int(iteration):
        errors.append("current_iteration must be non-negative")
    elif nonnegative_int(cap) and iteration > cap:
        errors.append("current_iteration cannot exceed cap")
    if not nonnegative_int(attempts):
        errors.append("attempts must be non-negative")

    criteria = data.get("criteria")
    criterion_states = []
    seen: set[str] = set()
    if not isinstance(criteria, list) or not criteria:
        errors.append("criteria must be a non-empty list")
    else:
        for index, criterion in enumerate(criteria):
            prefix = f"criteria[{index}]"
            if not isinstance(criterion, dict):
                errors.append(f"{prefix} must be an object")
                continue
            criterion_id = criterion.get("id")
            if not nonempty(criterion_id):
                errors.append(f"{prefix}.id must be non-empty")
            elif criterion_id in seen:
                errors.append(f"{prefix}.id duplicates {criterion_id!r}")
            else:
                seen.add(criterion_id)
            criterion_state = criterion.get("state")
            criterion_states.append(criterion_state)
            if criterion_state not in CRITERION_STATES:
                errors.append(
                    f"{prefix}.state must be one of {sorted(CRITERION_STATES)}"
                )
            if criterion_state in {"passed", "failed", "blocked"} and not nonempty(
                criterion.get("evidence")
            ):
                errors.append(f"{prefix}.evidence is required for resolved states")

    blockers = data.get("blockers")
    if not isinstance(blockers, list) or not all(nonempty(item) for item in blockers):
        errors.append("blockers must be a list of non-empty strings")
    next_action = data.get("next_action")
    if state == "in_progress" and not nonempty(next_action):
        errors.append("in_progress state requires next_action")
    if state in {"passed", "partial", "blocked"} and next_action is not None:
        errors.append("terminal state requires next_action=null")
    if state == "passed" and any(item != "passed" for item in criterion_states):
        errors.append("passed goal requires every criterion passed")
    if state == "passed" and blockers:
        errors.append("passed goal cannot retain blockers")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["goal"])
    parser.add_argument("state", nargs="?", type=Path)
    parser.add_argument("--print-template", action="store_true")
    args = parser.parse_args()
    if args.print_template:
        print(json.dumps(GOAL_TEMPLATE, indent=2))
        return 0
    if args.state is None:
        parser.error("state path is required unless --print-template is used")
    try:
        data = json.loads(args.state.read_text())
    except OSError as exc:
        print(f"ERROR: cannot read {args.state}: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}", file=sys.stderr)
        return 2
    errors = validate_goal(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: valid {args.kind} state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
