#!/usr/bin/env python3
"""
First-run key setup utility for dialectic-council.
Usage:
  python3 setup_keys.py          # interactive setup
  python3 setup_keys.py --check  # check only, exit 1 if no external models
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from model_client import KEYS_PATH, PROVIDERS, validate_key


def load_existing() -> dict:
    if KEYS_PATH.exists():
        try:
            return json.loads(KEYS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_keys(keys: dict) -> None:
    KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEYS_PATH.write_text(json.dumps(keys, indent=2))
    KEYS_PATH.chmod(0o600)


def print_council(keys: dict) -> None:
    print("\n── Assembled Council ─────────────────────────────")
    print("  ✓ claude  (always active — no key required)")
    for provider in PROVIDERS:
        if keys.get(provider):
            print(f"  ✓ {provider}")
        else:
            print(f"  ✗ {provider}  (no key)")
    print("──────────────────────────────────────────────────\n")


async def run_check() -> bool:
    """Return True if at least one external model key is configured."""
    keys = load_existing()
    active_external = [p for p in PROVIDERS if keys.get(p)]
    print_council(keys)
    if not active_external:
        print("No external model keys configured.")
        print(f"Run: python3 {__file__}  to add keys.\n")
        return False
    return True


async def run_setup() -> None:
    keys = load_existing()
    print("\n── Dialectic Council — Key Setup ─────────────────")
    print(f"Keys file: {KEYS_PATH}\n")

    for provider, cfg in PROVIDERS.items():
        current = keys.get(provider)
        masked = f"...{current[-6:]}" if current else "not set"
        prompt = (
            f"{provider} API key [{masked}] "
            f"(env: {cfg['key_env']}, Enter to skip): "
        )
        try:
            value = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            break

        if not value:
            continue

        print(f"  Validating {provider} key...", end=" ", flush=True)
        valid = await validate_key(provider, value)
        if valid:
            print("OK")
            keys[provider] = value
        else:
            print("FAILED — key rejected by API, not saved")

    save_keys(keys)
    print_council(keys)
    print(f"Keys saved to {KEYS_PATH}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        ok = asyncio.run(run_check())
        sys.exit(0 if ok else 1)
    else:
        asyncio.run(run_setup())
