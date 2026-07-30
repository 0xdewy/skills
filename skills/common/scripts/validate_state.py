#!/usr/bin/env python3
"""Validate durable status.json files for goal and project-manager runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


GOAL_STATES = {"pending", "in_progress", "passed", "partial", "blocked"}
CRITERION_STATES = {"pending", "passed", "failed", "blocked"}
PM_STATES = {"planned", "in_progress", "passed", "partial", "blocked"}
SLICE_STATES = {"pending", "ready", "in_progress", "review", "accepted", "blocked"}

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

PM_TEMPLATE = {
    "schema_version": 1,
    "mandate": "build tool",
    "mode": "standard",
    "state": "in_progress",
    "current_wave": 1,
    "acceptance": ["integration check passes"],
    "integration_checks": ["pytest"],
    "next_action": "dispatch cli",
    "slices": [
        {
            "id": "core",
            "dependencies": [],
            "state": "accepted",
            "attempts": 1,
            "artifact": "workers/core/SUMMARY.md",
            "evidence": "unit tests pass",
        },
        {
            "id": "cli",
            "dependencies": ["core"],
            "state": "ready",
            "attempts": 0,
        },
    ],
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
    if data.get("mode") not in {"lite", "standard", "full"}:
        errors.append("mode must be lite, standard, or full")
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


def cycle_nodes(dependencies: dict[str, list[str]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cyclic: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            cyclic.update(visiting)
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in dependencies.get(node, []):
            if dependency in dependencies:
                visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in dependencies:
        visit(node)
    return cyclic


def validate_project(data: Any, root: Path | None = None) -> list[str]:
    errors = validate_common(data)
    if errors or not isinstance(data, dict):
        return errors
    if not nonempty(data.get("mandate")):
        errors.append("mandate must be non-empty")
    if data.get("mode") not in {"quick", "standard", "thorough"}:
        errors.append("mode must be quick, standard, or thorough")
    state = data.get("state")
    if state not in PM_STATES:
        errors.append(f"state must be one of {sorted(PM_STATES)}")
    if not nonnegative_int(data.get("current_wave")):
        errors.append("current_wave must be non-negative")
    for field in ("acceptance", "integration_checks"):
        value = data.get(field)
        if not isinstance(value, list) or not value or not all(nonempty(x) for x in value):
            errors.append(f"{field} must be a non-empty list of strings")

    slices = data.get("slices")
    slice_map: dict[str, dict[str, Any]] = {}
    dependencies: dict[str, list[str]] = {}
    if not isinstance(slices, list) or not slices:
        errors.append("slices must be a non-empty list")
        slices = []
    for index, slice_ in enumerate(slices):
        prefix = f"slices[{index}]"
        if not isinstance(slice_, dict):
            errors.append(f"{prefix} must be an object")
            continue
        slice_id = slice_.get("id")
        if not nonempty(slice_id):
            errors.append(f"{prefix}.id must be non-empty")
            continue
        if slice_id in slice_map:
            errors.append(f"{prefix}.id duplicates {slice_id!r}")
        slice_map[slice_id] = slice_
        deps = slice_.get("dependencies")
        if not isinstance(deps, list) or not all(nonempty(dep) for dep in deps):
            errors.append(f"{prefix}.dependencies must be a list of IDs")
            deps = []
        elif len(deps) != len(set(deps)):
            errors.append(f"{prefix}.dependencies contains duplicates")
        dependencies[slice_id] = deps
        slice_state = slice_.get("state")
        if slice_state not in SLICE_STATES:
            errors.append(f"{prefix}.state must be one of {sorted(SLICE_STATES)}")
        if not nonnegative_int(slice_.get("attempts")):
            errors.append(f"{prefix}.attempts must be non-negative")
        if slice_state == "accepted":
            artifact = slice_.get("artifact")
            if not nonempty(artifact) or Path(artifact).is_absolute() or ".." in Path(artifact).parts:
                errors.append(f"{prefix}.artifact must be a safe relative path")
            elif root is not None and not (root / artifact).is_file():
                errors.append(f"{prefix}.artifact does not exist under root")
            if not nonempty(slice_.get("evidence")):
                errors.append(f"{prefix}.evidence is required when accepted")

    for slice_id, deps in dependencies.items():
        for dependency in deps:
            if dependency not in slice_map:
                errors.append(f"slice {slice_id!r} has unknown dependency {dependency!r}")
            if dependency == slice_id:
                errors.append(f"slice {slice_id!r} cannot depend on itself")
        slice_state = slice_map[slice_id].get("state")
        if slice_state in {"ready", "in_progress", "review", "accepted"}:
            unaccepted = [
                dependency
                for dependency in deps
                if dependency in slice_map
                and slice_map[dependency].get("state") != "accepted"
            ]
            if unaccepted:
                errors.append(
                    f"slice {slice_id!r} is {slice_state} before dependencies "
                    f"are accepted: {unaccepted}"
                )
    cyclic = cycle_nodes(dependencies)
    if cyclic:
        errors.append(f"slice dependency graph contains a cycle: {sorted(cyclic)}")

    next_action = data.get("next_action")
    if state == "in_progress" and not nonempty(next_action):
        errors.append("in_progress state requires next_action")
    if state in {"passed", "partial", "blocked"} and next_action is not None:
        errors.append("terminal state requires next_action=null")
    if state == "passed" and any(
        slice_.get("state") != "accepted" for slice_ in slice_map.values()
    ):
        errors.append("passed project requires every slice accepted")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["goal", "project-manager"])
    parser.add_argument("state", nargs="?", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--print-template", action="store_true")
    args = parser.parse_args()
    if args.print_template:
        print(json.dumps(GOAL_TEMPLATE if args.kind == "goal" else PM_TEMPLATE, indent=2))
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
    errors = (
        validate_goal(data)
        if args.kind == "goal"
        else validate_project(data, args.root)
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: valid {args.kind} state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
