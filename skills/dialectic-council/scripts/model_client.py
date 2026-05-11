"""
Unified async interface for calling Claude sub-agents and external model APIs.
All clients expose: async call(prompt: str) -> str
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


KEYS_PATH = Path.home() / ".claude" / "dialectic-keys.json"

PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "key_env": "DEEPSEEK_API_KEY",
    },
    "minimax": {
        "base_url": "https://api.minimax.chat/v1",
        "default_model": "abab6.5s-chat",
        "key_env": "MINIMAX_API_KEY",
        "group_id_env": "MINIMAX_GROUP_ID",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "key_env": "OPENAI_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.0-flash",
        "key_env": "GEMINI_API_KEY",
    },
}


def load_keys() -> dict:
    """Load API keys from ~/.claude/dialectic-keys.json, falling back to env vars."""
    keys = {}
    if KEYS_PATH.exists():
        try:
            keys = json.loads(KEYS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    for provider, cfg in PROVIDERS.items():
        env_val = os.environ.get(cfg["key_env"])
        if env_val and not keys.get(provider):
            keys[provider] = env_val

    group_id_env = os.environ.get("MINIMAX_GROUP_ID")
    if group_id_env:
        keys["minimax_group_id"] = group_id_env

    return keys


def build_council(requested: Optional[list[str]] = None) -> list["ModelClient"]:
    """
    Build the council from available keys.
    Claude is always included. External models are added when keys are present.
    requested: optional list of provider names to restrict to.
    """
    keys = load_keys()
    council: list[ModelClient] = [ClaudeClient()]

    for provider, cfg in PROVIDERS.items():
        if requested and provider not in requested:
            continue
        api_key = keys.get(provider)
        if api_key:
            group_id = keys.get("minimax_group_id") if provider == "minimax" else None
            council.append(OpenAICompatClient(
                name=provider,
                api_key=api_key,
                base_url=cfg["base_url"],
                model=cfg["default_model"],
                group_id=group_id,
            ))

    return council


class ModelClient:
    name: str

    async def call(self, prompt: str, system: Optional[str] = None) -> str:
        raise NotImplementedError


class ClaudeClient(ModelClient):
    name = "claude"

    async def call(self, prompt: str, system: Optional[str] = None) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["claude", "--print", "--dangerously-skip-permissions"],
                input=full_prompt,
                capture_output=True,
                text=True,
            ),
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude subprocess failed: {result.stderr[:500]}")
        return result.stdout.strip()


class OpenAICompatClient(ModelClient):
    def __init__(self, name: str, api_key: str, base_url: str, model: str, group_id: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.group_id = group_id

    async def call(self, prompt: str, system: Optional[str] = None) -> str:
        if httpx is None:
            raise ImportError("httpx is required for external model calls: pip install httpx")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        request_data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }
        if self.name == "minimax" and self.group_id:
            request_data["group_id"] = self.group_id

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_data,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()


async def validate_key(provider: str, api_key: str) -> bool:
    """Quick validation: send a minimal prompt and check for a response."""
    cfg = PROVIDERS.get(provider)
    if not cfg:
        return False
    client = OpenAICompatClient(
        name=provider,
        api_key=api_key,
        base_url=cfg["base_url"],
        model=cfg["default_model"],
    )
    try:
        result = await client.call("Reply with the single word: OK")
        return bool(result)
    except Exception:
        return False
