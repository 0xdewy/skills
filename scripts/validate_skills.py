#!/usr/bin/env python3
"""Lightweight repository validation for skill metadata and eval contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

META_SKILLS = {
    "goal",
    "project-manager",
    "red-team",
    "code-smellz",
    "pr-smellz",
    "shrinkray",
}

FORBIDDEN_ACTIVE_TEXT = [
    "evm-auditor",
    "direct-executor",
    "domain-router",
    "god-skill",
    "brainstormers",
    "startup-ideation",
    "simple-memory",
    "coders",
    "one-shot-project",
    "implementer",
]

MAX_SKILL_BYTES = 5_000
MAX_DESCRIPTION_CHARS = 450
MAX_PROMPT_BYTES = 12_000
ACTIVATION_MODES = ("namespace", "intent", "explicit")
PROMPT_TYPES = ("forced", "activation", "anti_trigger")
ACTIVATION_DESCRIPTION_LIMITS = {
    "namespace": 260,
    "explicit": 300,
    "intent": MAX_DESCRIPTION_CHARS,
}
RESOURCE_REF_RE = re.compile(r"`((?:\.\./common|references|scripts)/[^`\s,;)]+)`")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        fail(f"{path.relative_to(ROOT)} missing YAML frontmatter")

    data: dict[str, str] = {}
    lines = match.group(1).splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value in {">", ">-", "|", "|-"}:
            index += 1
            block = []
            while index < len(lines) and lines[index].startswith("  "):
                block.append(lines[index].strip())
                index += 1
            data[key] = " ".join(block)
            continue
        data[key] = value
        index += 1
    return data


def token_count(text: str) -> tuple[int, str]:
    """Use cl100k when installed; otherwise return a clearly labeled estimate."""
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text)), "cl100k_base"
    except ImportError:
        return (len(text) + 3) // 4, "approx_chars_div_4"


def validate_fixture_files(eval_file: Path, index: int, fixtures) -> None:
    if not isinstance(fixtures, dict):
        fail(f"{eval_file.relative_to(ROOT)} eval #{index} fixture_files must be an object")
    for raw_path, body in fixtures.items():
        if not isinstance(raw_path, str) or not raw_path:
            fail(f"{eval_file.relative_to(ROOT)} eval #{index} has an empty fixture path")
        path = Path(raw_path)
        if path.is_absolute() or ".." in path.parts:
            fail(f"{eval_file.relative_to(ROOT)} eval #{index} has unsafe fixture path {raw_path!r}")
        if body is not None and not isinstance(body, str):
            fail(
                f"{eval_file.relative_to(ROOT)} eval #{index} fixture {raw_path!r} "
                "must contain text or null"
            )


def main() -> int:
    if not SKILLS.is_dir():
        fail("skills/ directory not found")

    skill_files = sorted(SKILLS.glob("*/SKILL.md"))
    if not skill_files:
        fail("no skills/*/SKILL.md files found")

    description_chars = 0
    body_chars = 0
    description_texts = []
    body_texts = []
    activation_counts = {mode: 0 for mode in ACTIVATION_MODES}
    for skill in skill_files:
        rel = skill.relative_to(ROOT)
        text = skill.read_text()
        frontmatter = parse_frontmatter(skill)
        frontmatter_text = text.split("---", 2)[1]
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        activation = frontmatter.get("activation")
        disabled = frontmatter.get("disable-model-invocation") == "true"
        composable = frontmatter.get("composable") == "true"

        if not name:
            fail(f"{rel} missing frontmatter name")
        if not description:
            fail(f"{rel} missing frontmatter description")
        if len(name) > 64 or not re.fullmatch(r"[a-z0-9-]+", name):
            fail(f"{rel} name must be <=64 lowercase letters, numbers, or hyphens")
        if "<" in name or ">" in name or "<" in description or ">" in description:
            fail(f"{rel} name/description may not contain XML tags")
        if activation not in ACTIVATION_MODES:
            fail(
                f"{rel} metadata.activation must be one of "
                f"{sorted(ACTIVATION_MODES)}, got {activation!r}"
            )
        if not re.search(rf"^  activation:\s*{re.escape(activation)}\s*$", frontmatter_text, re.M):
            fail(f"{rel} activation must be declared under metadata")
        description_limit = ACTIVATION_DESCRIPTION_LIMITS[activation]
        if len(description) > description_limit:
            fail(
                f"{rel} description is {len(description)} chars; "
                f"keep {activation} routing metadata under {description_limit}"
            )
        if activation == "intent":
            if "TRIGGER" not in description or "SKIP" not in description:
                fail(f"{rel} intent mode requires TRIGGER and SKIP boundaries")
        elif "TRIGGER" in description or "SKIP" in description:
            fail(f"{rel} {activation} mode must not carry TRIGGER/SKIP lists")
        if activation == "explicit" and "only use when explicitly" not in description.lower():
            fail(f"{rel} explicit mode must say 'Only use when explicitly requested'")
        if activation == "explicit" and disabled == composable:
            fail(
                f"{rel} explicit mode requires exactly one of "
                "disable-model-invocation: true or metadata.composable: true"
            )
        if activation != "explicit" and (disabled or composable):
            fail(f"{rel} invocation policy fields are only valid for explicit mode")
        if activation == "namespace":
            parts = [re.sub(r"v?\d+$", "", part) for part in re.split(r"[-_]", name)]
            if not any(part and part.lower() in description.lower() for part in parts):
                fail(f"{rel} namespace description must name its domain")
        if name != skill.parent.name:
            fail(f"{rel} name {name!r} does not match directory {skill.parent.name!r}")
        if "[TODO" in text or "TODO:" in text:
            fail(f"{rel} contains template TODO text")
        if skill.stat().st_size > MAX_SKILL_BYTES:
            fail(f"{rel} is {skill.stat().st_size} bytes; keep SKILL.md under {MAX_SKILL_BYTES}")
        if name in META_SKILLS and "../common/ROUTING.md" not in text:
            fail(f"{rel} is a meta-skill but does not reference ../common/ROUTING.md")
        reference_dir = skill.parent / "references"
        docs = [skill]
        if reference_dir.exists():
            docs.extend(reference_dir.rglob("*.md"))
        for doc in docs:
            if doc.name == "example-skill.md":
                continue
            for resource in RESOURCE_REF_RE.findall(doc.read_text(errors="replace")):
                resource = resource.rstrip(".:")
                if any(marker in resource for marker in ("<", ">", "{", "}", "*")):
                    continue
                if not (skill.parent / resource).resolve().exists():
                    fail(
                        f"{doc.relative_to(ROOT)} references missing local resource "
                        f"{resource!r}"
                    )
        description_chars += len(description)
        body = text.split("---", 2)[-1]
        body_chars += len(body)
        description_texts.append(description)
        body_texts.append(body)
        activation_counts[activation] += 1

    prompt_files = sorted(SKILLS.glob("*/references/*prompt*.md"))
    for prompt in prompt_files:
        if prompt.stat().st_size > MAX_PROMPT_BYTES:
            fail(
                f"{prompt.relative_to(ROOT)} is {prompt.stat().st_size} bytes; "
                f"split prompt bundles above {MAX_PROMPT_BYTES}"
            )

    routing = (SKILLS / "common" / "ROUTING.md").read_text()
    active_text = routing + "\n".join(p.read_text() for p in skill_files)
    for forbidden in FORBIDDEN_ACTIVE_TEXT:
        if forbidden in active_text:
            fail(f"active skill/routing text contains stale term: {forbidden}")

    eval_count = 0
    routing_coverage = {}
    for eval_file in sorted(SKILLS.glob("*/evals/evals.json")):
        try:
            data = json.loads(eval_file.read_text())
        except json.JSONDecodeError as exc:
            fail(f"{eval_file.relative_to(ROOT)} invalid JSON: {exc}")

        if isinstance(data, dict):
            declared_name = data.get("skill_name")
            if declared_name is not None and declared_name != eval_file.parents[1].name:
                fail(
                    f"{eval_file.relative_to(ROOT)} skill_name {declared_name!r} "
                    f"does not match directory {eval_file.parents[1].name!r}"
                )
            evals = data.get("evals")
            if not isinstance(evals, list):
                fail(f"{eval_file.relative_to(ROOT)} object eval file missing evals list")
        elif isinstance(data, list):
            evals = data
        else:
            fail(f"{eval_file.relative_to(ROOT)} must be a list or object with evals")

        seen_ids = set()
        case_types = set()
        for index, case in enumerate(evals, start=1):
            if not isinstance(case, dict):
                fail(f"{eval_file.relative_to(ROOT)} eval #{index} is not an object")
            eval_id = case.get("id")
            if eval_id is None:
                fail(f"{eval_file.relative_to(ROOT)} eval #{index} missing id")
            if eval_id in seen_ids:
                fail(f"{eval_file.relative_to(ROOT)} duplicate eval id {eval_id!r}")
            seen_ids.add(eval_id)
            for field in ("prompt", "expected_output", "expectations"):
                if field not in case:
                    fail(f"{eval_file.relative_to(ROOT)} eval #{index} missing {field}")
            if not isinstance(case["expectations"], list) or not case["expectations"]:
                fail(f"{eval_file.relative_to(ROOT)} eval #{index} expectations must be non-empty list")
            if "outcome_expectations" in case:
                outcomes = case["outcome_expectations"]
                if not isinstance(outcomes, list) or not outcomes or not all(
                    isinstance(item, str) and item.strip() for item in outcomes
                ):
                    fail(
                        f"{eval_file.relative_to(ROOT)} eval #{index} "
                        "outcome_expectations must be a non-empty string list"
                    )
                if "outcome_expected" in case and not isinstance(case["outcome_expected"], str):
                    fail(
                        f"{eval_file.relative_to(ROOT)} eval #{index} "
                        "outcome_expected must be text"
                    )
            for field in ("required_regex", "forbidden_regex", "required_files", "manual_checks"):
                if field in case and not isinstance(case[field], list):
                    fail(f"{eval_file.relative_to(ROOT)} eval #{index} {field} must be a list")
            for field in ("required_regex", "forbidden_regex"):
                for pattern in case.get(field, []):
                    if not isinstance(pattern, str):
                        fail(f"{eval_file.relative_to(ROOT)} eval #{index} {field} entry is not a string")
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        fail(f"{eval_file.relative_to(ROOT)} eval #{index} invalid regex {pattern!r}: {exc}")
            case_type = case.get("prompt_type", "forced")
            if case_type not in PROMPT_TYPES:
                fail(
                    f"{eval_file.relative_to(ROOT)} eval #{index} has unknown "
                    f"prompt_type {case_type!r}"
                )
            case_types.add(case_type)
            if "fixture_files" in case:
                validate_fixture_files(eval_file, index, case["fixture_files"])
            if case.get("context") and case_type != "anti_trigger" and not case.get("fixture_files"):
                fail(
                    f"{eval_file.relative_to(ROOT)} eval #{index} has context but no "
                    "materialized fixture_files"
                )
            eval_count += 1
        routing_coverage[eval_file.parents[1].name] = case_types

    real_activation_modes = set()
    for skill_file in skill_files:
        name = skill_file.parent.name
        if name not in routing_coverage:
            fail(f"skills/{name} has no evals/evals.json")
        modes = routing_coverage[name]
        if "activation" in modes:
            real_activation_modes.add(parse_frontmatter(skill_file).get("activation"))
        if "anti_trigger" not in modes and parse_frontmatter(skill_file).get("activation") != "namespace":
            fail(f"skills/{name} has no anti_trigger eval")

    declared_modes = {
        parse_frontmatter(path).get("activation") for path in skill_files
        if parse_frontmatter(path).get("disable-model-invocation") != "true"
    }
    missing_real_modes = declared_modes - real_activation_modes
    if missing_real_modes:
        fail(f"raw positive activation evals do not cover modes {sorted(missing_real_modes)}")

    reference_paths = [
        path for path in SKILLS.glob("*/references/**/*") if path.is_file()
    ]
    reference_text = "\n".join(
        path.read_text(errors="replace") for path in reference_paths
    )
    description_tokens, token_method = token_count("\n".join(description_texts))
    body_tokens, _ = token_count("\n".join(body_texts))
    reference_tokens, _ = token_count(reference_text)
    print(
        f"OK: {len(skill_files)} skills, {eval_count} evals; "
        f"activation={activation_counts}; "
        f"tokens[{token_method}] descriptions={description_tokens}, "
        f"activated_bodies={body_tokens}, lazy_references={reference_tokens}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
