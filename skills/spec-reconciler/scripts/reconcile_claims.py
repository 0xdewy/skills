#!/usr/bin/env python3
"""Validate a claim ledger and classify cross-surface specification drift."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROLES = {"primary", "derived", "observed"}
EDIT_STRATEGIES = {"report-only", "patch", "regenerate"}
LOCATION_RE = re.compile(r"^.+:\d+$")
AUTHORITY_SOURCE_RE = re.compile(r"^(?:.+:\d+|user:.+)$")

TEMPLATE = {
    "schema_version": 1,
    "target": "http:GET /widgets/{id}",
    "authority_policy": {
        "source": "AGENTS.md:12",
        "description": "The public schema is authoritative; clients are generated.",
    },
    "surfaces": [
        {
            "id": "schema",
            "kind": "openapi",
            "path": "openapi.yaml",
            "role": "primary",
            "authority_rank": 1,
            "edit_strategy": "report-only",
        },
        {
            "id": "client",
            "kind": "generated-client",
            "path": "src/client.py",
            "role": "derived",
            "authority_rank": 2,
            "edit_strategy": "regenerate",
            "update_command": "python scripts/generate_client.py",
        },
    ],
    "claims": [
        {
            "id": "CLM-001",
            "key": "http:GET /widgets/{id}.response.200.body.id.type",
            "value": "string",
            "surface": "schema",
            "location": "openapi.yaml:42",
            "evidence": "The response schema declares id as a string.",
        },
        {
            "id": "CLM-002",
            "key": "http:GET /widgets/{id}.response.200.body.id.type",
            "value": "string",
            "surface": "client",
            "location": "src/client.py:8",
            "evidence": "The generated client types id as str.",
        },
    ],
    "expectations": [
        {
            "key": "http:GET /widgets/{id}.response.200.body.id.type",
            "surfaces": ["schema", "client"],
            "reason": "The generation policy covers public response fields.",
        }
    ],
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def positive_int_or_none(value: Any) -> bool:
    return value is None or (
        isinstance(value, int) and not isinstance(value, bool) and value > 0
    )


def validate(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["ledger root must be an object"]

    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not nonempty(data.get("target")):
        errors.append("target must be a non-empty string")

    policy = data.get("authority_policy")
    policy_source = None
    if not isinstance(policy, dict):
        errors.append("authority_policy must be an object")
    else:
        policy_source = policy.get("source")
        if policy_source is not None and not nonempty(policy_source):
            errors.append("authority_policy.source must be null or non-empty")
        elif nonempty(policy_source) and not AUTHORITY_SOURCE_RE.fullmatch(
            policy_source
        ):
            errors.append(
                "authority_policy.source must use path:line or user:<decision>"
            )
        if not nonempty(policy.get("description")):
            errors.append("authority_policy.description must be non-empty")

    surfaces = data.get("surfaces")
    surface_map: dict[str, dict[str, Any]] = {}
    if not isinstance(surfaces, list) or not surfaces:
        errors.append("surfaces must be a non-empty list")
    else:
        for index, surface in enumerate(surfaces):
            prefix = f"surfaces[{index}]"
            if not isinstance(surface, dict):
                errors.append(f"{prefix} must be an object")
                continue
            for field in ("id", "kind", "path"):
                if not nonempty(surface.get(field)):
                    errors.append(f"{prefix}.{field} must be non-empty")
            surface_id = surface.get("id")
            if nonempty(surface_id):
                if surface_id in surface_map:
                    errors.append(f"{prefix}.id duplicates {surface_id!r}")
                surface_map[surface_id] = surface
            role = surface.get("role")
            strategy = surface.get("edit_strategy")
            rank = surface.get("authority_rank")
            if role not in ROLES:
                errors.append(f"{prefix}.role must be one of {sorted(ROLES)}")
            if strategy not in EDIT_STRATEGIES:
                errors.append(
                    f"{prefix}.edit_strategy must be one of "
                    f"{sorted(EDIT_STRATEGIES)}"
                )
            if not positive_int_or_none(rank):
                errors.append(f"{prefix}.authority_rank must be positive or null")
            if policy_source is None and rank is not None:
                errors.append(
                    f"{prefix}.authority_rank must be null without a policy source"
                )
            if role != "derived" and strategy != "report-only":
                errors.append(
                    f"{prefix} non-derived surfaces must use report-only"
                )
            if strategy == "regenerate" and not nonempty(
                surface.get("update_command")
            ):
                errors.append(
                    f"{prefix}.update_command is required for regenerate"
                )

    claims = data.get("claims")
    if not isinstance(claims, list):
        errors.append("claims must be a list")
        claims = []
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        prefix = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("id", "key", "surface", "location", "evidence"):
            if not nonempty(claim.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty")
        if "value" not in claim:
            errors.append(f"{prefix}.value is required (null is allowed)")
        claim_id = claim.get("id")
        if nonempty(claim_id):
            if claim_id in claim_ids:
                errors.append(f"{prefix}.id duplicates {claim_id!r}")
            claim_ids.add(claim_id)
        surface_id = claim.get("surface")
        if nonempty(surface_id) and surface_id not in surface_map:
            errors.append(f"{prefix}.surface references unknown {surface_id!r}")
        location = claim.get("location")
        if nonempty(location) and not LOCATION_RE.fullmatch(location):
            errors.append(f"{prefix}.location must use path:line")
        try:
            json.dumps(claim.get("value"), sort_keys=True)
        except (TypeError, ValueError):
            errors.append(f"{prefix}.value must be JSON-serializable")

    expectations = data.get("expectations", [])
    if not isinstance(expectations, list):
        errors.append("expectations must be a list")
        expectations = []
    expectation_keys: set[str] = set()
    for index, expectation in enumerate(expectations):
        prefix = f"expectations[{index}]"
        if not isinstance(expectation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        key = expectation.get("key")
        if not nonempty(key):
            errors.append(f"{prefix}.key must be non-empty")
        elif key in expectation_keys:
            errors.append(f"{prefix}.key duplicates {key!r}")
        else:
            expectation_keys.add(key)
        expected_surfaces = expectation.get("surfaces")
        if not isinstance(expected_surfaces, list) or not expected_surfaces:
            errors.append(f"{prefix}.surfaces must be a non-empty list")
        else:
            seen_surfaces: set[str] = set()
            for surface_id in expected_surfaces:
                if not nonempty(surface_id):
                    errors.append(
                        f"{prefix}.surfaces entries must be non-empty strings"
                    )
                    continue
                if surface_id in seen_surfaces:
                    errors.append(f"{prefix}.surfaces contains duplicates")
                seen_surfaces.add(surface_id)
                if surface_id not in surface_map:
                    errors.append(
                        f"{prefix}.surfaces references unknown {surface_id!r}"
                    )
        if not nonempty(expectation.get("reason")):
            errors.append(f"{prefix}.reason must be non-empty")
    return errors


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def claim_view(claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": claim["id"],
        "surface": claim["surface"],
        "value": claim["value"],
        "location": claim["location"],
    }


def target_actions(
    target_ids: list[str], surfaces: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    actions = []
    for surface_id in target_ids:
        surface = surfaces[surface_id]
        action = {
            "surface": surface_id,
            "path": surface["path"],
            "strategy": surface["edit_strategy"],
        }
        if surface.get("update_command"):
            action["update_command"] = surface["update_command"]
        actions.append(action)
    return actions


def authoritative_claims(
    claims: list[dict[str, Any]],
    surfaces: dict[str, dict[str, Any]],
    policy_source: str | None,
) -> list[dict[str, Any]]:
    if not claims or policy_source is None:
        return []
    ranks = [surfaces[claim["surface"]]["authority_rank"] for claim in claims]
    if any(rank is None for rank in ranks):
        return []
    top_rank = min(ranks)
    top_claims = [
        claim
        for claim in claims
        if surfaces[claim["surface"]]["authority_rank"] == top_rank
    ]
    if len({canonical(claim["value"]) for claim in top_claims}) != 1:
        return []
    return top_claims


def classify_claim_group(
    key: str,
    claims: list[dict[str, Any]],
    surfaces: dict[str, dict[str, Any]],
    policy_source: str | None,
) -> dict[str, Any] | None:
    by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        by_surface[claim["surface"]].append(claim)
    internally_conflicting = sorted(
        surface_id
        for surface_id, surface_claims in by_surface.items()
        if len({canonical(claim["value"]) for claim in surface_claims}) > 1
    )
    if internally_conflicting:
        return {
            "key": key,
            "classification": "intra-surface-conflict",
            "claims": [claim_view(claim) for claim in claims],
            "conflicting_surface_ids": internally_conflicting,
            "target_surface_ids": internally_conflicting,
            "target_actions": target_actions(internally_conflicting, surfaces),
            "fixable": False,
        }

    values = {canonical(claim["value"]) for claim in claims}
    if len(values) < 2:
        return None

    base = {
        "key": key,
        "claims": [claim_view(claim) for claim in claims],
        "fixable": False,
        "target_surface_ids": [],
    }
    ranks = [surfaces[claim["surface"]]["authority_rank"] for claim in claims]
    if policy_source is None or any(rank is None for rank in ranks):
        return {**base, "classification": "ambiguous-authority"}

    top_claims = authoritative_claims(claims, surfaces, policy_source)
    if not top_claims:
        return {**base, "classification": "authority-conflict"}

    authoritative_value = top_claims[0]["value"]
    divergent = [
        claim
        for claim in claims
        if canonical(claim["value"]) != canonical(authoritative_value)
    ]
    targets = sorted({claim["surface"] for claim in divergent})
    derived_only = all(surfaces[target]["role"] == "derived" for target in targets)
    editable = derived_only and all(
        surfaces[target]["edit_strategy"] in {"patch", "regenerate"}
        for target in targets
    )
    classification = "stale-derived" if derived_only else "cross-surface-conflict"
    return {
        **base,
        "classification": classification,
        "authoritative_value": authoritative_value,
        "authoritative_claim_ids": [claim["id"] for claim in top_claims],
        "target_surface_ids": targets,
        "target_actions": target_actions(targets, surfaces),
        "fixable": editable,
    }


def reconcile(data: dict[str, Any]) -> dict[str, Any]:
    surfaces = {surface["id"]: surface for surface in data["surfaces"]}
    policy_source = data["authority_policy"]["source"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in data["claims"]:
        groups[claim["key"]].append(claim)

    conflicts: list[dict[str, Any]] = []
    consistent_keys = 0
    for key in sorted(groups):
        conflict = classify_claim_group(key, groups[key], surfaces, policy_source)
        if conflict is None:
            consistent_keys += 1
        else:
            conflicts.append(conflict)

    for expectation in sorted(data.get("expectations", []), key=lambda item: item["key"]):
        existing = groups.get(expectation["key"], [])
        present = {claim["surface"] for claim in existing}
        missing = sorted(set(expectation["surfaces"]) - present)
        if not missing:
            continue
        source_claims = authoritative_claims(existing, surfaces, policy_source)
        source_rank = (
            surfaces[source_claims[0]["surface"]]["authority_rank"]
            if source_claims
            else None
        )
        editable = all(
            surfaces[surface_id]["role"] == "derived"
            and surfaces[surface_id]["edit_strategy"] in {"patch", "regenerate"}
            and source_rank is not None
            and surfaces[surface_id]["authority_rank"] is not None
            and surfaces[surface_id]["authority_rank"] > source_rank
            for surface_id in missing
        )
        omission = {
            "key": expectation["key"],
            "classification": "omission",
            "claims": [claim_view(claim) for claim in existing],
            "missing_surface_ids": missing,
            "reason": expectation["reason"],
            "target_surface_ids": missing,
            "target_actions": target_actions(missing, surfaces),
            "fixable": bool(source_claims) and editable,
        }
        if source_claims:
            omission["authoritative_value"] = source_claims[0]["value"]
            omission["authoritative_claim_ids"] = [
                claim["id"] for claim in source_claims
            ]
        conflicts.append(omission)

    conflicts.sort(key=lambda item: (item["key"], item["classification"]))
    counts = Counter(item["classification"] for item in conflicts)
    return {
        "schema_version": 1,
        "target": data["target"],
        "authority_policy": data["authority_policy"],
        "summary": {
            "surfaces": len(data["surfaces"]),
            "claims": len(data["claims"]),
            "consistent_keys": consistent_keys,
            "conflicts": len(conflicts),
            "by_classification": dict(sorted(counts.items())),
        },
        "conflicts": conflicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--print-template", action="store_true")
    args = parser.parse_args()

    if args.print_template:
        print(json.dumps(TEMPLATE, indent=2))
        return 0
    if args.ledger is None:
        parser.error("ledger is required unless --print-template is used")

    try:
        data = json.loads(args.ledger.read_text())
    except OSError as exc:
        print(f"ERROR: cannot read {args.ledger}: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}", file=sys.stderr)
        return 2

    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    result = reconcile(data)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
        print(
            f"OK: {result['summary']['claims']} claims, "
            f"{result['summary']['conflicts']} conflicts -> {args.output}"
        )
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
