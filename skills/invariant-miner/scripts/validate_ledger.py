#!/usr/bin/env python3
"""Validate an invariant-miner INVARIANTS.json artifact."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


STATUSES = {"supported", "falsified", "rejected", "blocked"}
BASES = {"contract", "derived", "observed"}
CONFIDENCES = {"high", "medium", "low"}
METHODS = {
    "boundary",
    "exhaustive",
    "property",
    "metamorphic",
    "differential",
    "stateful",
    "fuzz",
    "static",
}
RESULTS = {"pass", "fail", "blocked", "not-run"}
SOURCE_RE = re.compile(r"^(?:.+:\d+|user:.+)$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

TEMPLATE = {
    "schema_version": 1,
    "target": "path:symbol",
    "seed": "recorded-seed",
    "budget": {"case_limit": 100, "time_limit_seconds": 30},
    "invariants": [
        {
            "id": "INV-001",
            "statement": "For all valid inputs satisfying P, Q holds.",
            "scope": "path:symbol",
            "status": "supported",
            "basis": "derived",
            "confidence": "medium",
            "evidence": [{"source": "contract.md:1", "claim": "Evidence claim"}],
            "falsification": {
                "method": "property",
                "command": "test command",
                "result": "pass",
                "receipt": {
                    "exit_code": 0,
                    "cases_executed": 100,
                    "duration_ms": 250,
                    "output_sha256": "0" * 64,
                },
            },
            "durable_test": True,
            "test_path": "tests/test_target.py",
        }
    ],
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def concrete(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict, tuple, set)):
        return bool(value)
    return True


def validate_record(record: Any, index: int) -> list[str]:
    prefix = f"invariants[{index}]"
    if not isinstance(record, dict):
        return [f"{prefix} must be an object"]

    errors: list[str] = []
    for field in ("id", "statement", "scope"):
        if not nonempty(record.get(field)):
            errors.append(f"{prefix}.{field} must be a non-empty string")

    status = record.get("status")
    basis = record.get("basis")
    confidence = record.get("confidence")
    if status not in STATUSES:
        errors.append(f"{prefix}.status must be one of {sorted(STATUSES)}")
    if basis not in BASES:
        errors.append(f"{prefix}.basis must be one of {sorted(BASES)}")
    if confidence not in CONFIDENCES:
        errors.append(
            f"{prefix}.confidence must be one of {sorted(CONFIDENCES)}"
        )

    evidence = record.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{prefix}.evidence must be a non-empty list")
    else:
        for evidence_index, item in enumerate(evidence):
            item_prefix = f"{prefix}.evidence[{evidence_index}]"
            if not isinstance(item, dict):
                errors.append(f"{item_prefix} must be an object")
                continue
            for field in ("source", "claim"):
                if not nonempty(item.get(field)):
                    errors.append(f"{item_prefix}.{field} must be non-empty")
            source = item.get("source")
            if nonempty(source) and not SOURCE_RE.fullmatch(source):
                errors.append(
                    f"{item_prefix}.source must use path:line or user:<decision>"
                )

    falsification = record.get("falsification")
    if status in {"supported", "falsified"} and not isinstance(
        falsification, dict
    ):
        errors.append(
            f"{prefix}.falsification must be an object for {status} invariants"
        )
    elif falsification is not None and not isinstance(falsification, dict):
        errors.append(f"{prefix}.falsification must be an object or null")
    elif isinstance(falsification, dict):
        method = falsification.get("method")
        result = falsification.get("result")
        if method not in METHODS:
            errors.append(
                f"{prefix}.falsification.method must be one of {sorted(METHODS)}"
            )
        if result not in RESULTS:
            errors.append(
                f"{prefix}.falsification.result must be one of {sorted(RESULTS)}"
            )
        if result != "not-run" and not nonempty(falsification.get("command")):
            errors.append(f"{prefix}.falsification.command must be non-empty")
        if status == "supported" and result != "pass":
            errors.append(f"{prefix} supported invariant must have result=pass")
        if status == "falsified" and result != "fail":
            errors.append(f"{prefix} falsified invariant must have result=fail")
        receipt = falsification.get("receipt")
        if status in {"supported", "falsified"} and not isinstance(receipt, dict):
            errors.append(
                f"{prefix}.falsification.receipt is required for executed results"
            )
        elif isinstance(receipt, dict):
            exit_code = receipt.get("exit_code")
            cases = receipt.get("cases_executed")
            duration = receipt.get("duration_ms")
            digest = receipt.get("output_sha256")
            if not isinstance(exit_code, int) or isinstance(exit_code, bool):
                errors.append(f"{prefix}.falsification.receipt.exit_code must be int")
            if not isinstance(cases, int) or isinstance(cases, bool) or cases <= 0:
                errors.append(
                    f"{prefix}.falsification.receipt.cases_executed must be positive"
                )
            if (
                not isinstance(duration, int)
                or isinstance(duration, bool)
                or duration < 0
            ):
                errors.append(
                    f"{prefix}.falsification.receipt.duration_ms must be non-negative"
                )
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                errors.append(
                    f"{prefix}.falsification.receipt.output_sha256 must be 64 hex chars"
                )
            if result == "pass" and exit_code != 0:
                errors.append(f"{prefix} pass receipt must have exit_code=0")
            if result == "fail" and exit_code == 0:
                errors.append(f"{prefix} fail receipt must have nonzero exit_code")
            if status == "falsified" and not nonempty(
                receipt.get("reproduction_command")
            ):
                errors.append(
                    f"{prefix} falsified invariant requires reproduction_command"
                )

    if status == "falsified" and not concrete(record.get("counterexample")):
        errors.append(
            f"{prefix} falsified invariant requires a concrete counterexample"
        )
    if status == "rejected" and not nonempty(record.get("rejection_reason")):
        errors.append(f"{prefix} rejected invariant requires rejection_reason")
    if status == "blocked" and not nonempty(record.get("blocked_reason")):
        errors.append(f"{prefix} blocked invariant requires blocked_reason")
    durable_test = record.get("durable_test")
    if durable_test is not None and not isinstance(durable_test, bool):
        errors.append(f"{prefix}.durable_test must be a boolean when present")
    if durable_test is True and not nonempty(record.get("test_path")):
        errors.append(f"{prefix}.test_path is required for a durable test")
    if basis == "observed" and durable_test is True:
        if not nonempty(record.get("policy_authorization")):
            errors.append(
                f"{prefix} observed invariant with durable_test=true requires "
                "policy_authorization"
            )
    return errors


def validate(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["ledger root must be an object"]

    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not nonempty(data.get("target")):
        errors.append("target must be a non-empty string")
    if not nonempty(data.get("seed")):
        errors.append("seed must be a non-empty string")
    budget = data.get("budget")
    if not isinstance(budget, dict):
        errors.append("budget must be an object")
    else:
        limits = (budget.get("case_limit"), budget.get("time_limit_seconds"))
        if not any(
            isinstance(value, int) and not isinstance(value, bool) and value > 0
            for value in limits
        ):
            errors.append(
                "budget requires a positive integer case_limit or time_limit_seconds"
            )
    invariants = data.get("invariants")
    if not isinstance(invariants, list):
        errors.append("invariants must be a list")
        return errors

    seen: set[str] = set()
    for index, record in enumerate(invariants):
        errors.extend(validate_record(record, index))
        if isinstance(record, dict) and nonempty(record.get("id")):
            record_id = record["id"]
            if record_id in seen:
                errors.append(f"invariants[{index}].id duplicates {record_id!r}")
            seen.add(record_id)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", nargs="?", type=Path)
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
    print(f"OK: {len(data['invariants'])} invariant records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
