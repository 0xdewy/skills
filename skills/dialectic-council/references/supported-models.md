# Supported Models

All external providers use the OpenAI-compatible chat completions API format.
Add a new provider by extending `PROVIDERS` in `scripts/model_client.py`.

---

## Claude (built-in)

Always active. No API key required — uses the local `claude` CLI.

- **Client:** `ClaudeClient` — spawns `claude --print --dangerously-skip-permissions`
- **Model:** whatever Claude version is installed
- **Rate limit:** n/a (local subprocess)

---

## DeepSeek

| Field | Value |
|---|---|
| Base URL | `https://api.deepseek.com/v1` |
| Default model | `deepseek-chat` (DeepSeek-V3) |
| Key env var | `DEEPSEEK_API_KEY` |
| Keys file key | `deepseek` |
| Auth header | `Authorization: Bearer <key>` |
| Docs | https://platform.deepseek.com/api-docs |

**Alternative models:** `deepseek-reasoner` (DeepSeek-R1, slower, chain-of-thought)

---

## MiniMax

| Field | Value |
|---|---|
| Base URL | `https://api.minimax.chat/v1` |
| Default model | `abab6.5s-chat` |
| Key env var | `MINIMAX_API_KEY` |
| Keys file key | `minimax` |
| Auth header | `Authorization: Bearer <key>` |
| Docs | https://platform.minimaxi.com/document/ChatCompletion |

**Alternative models:** `abab6.5-chat` (larger, slower)

---

## OpenAI

| Field | Value |
|---|---|
| Base URL | `https://api.openai.com/v1` |
| Default model | `gpt-4o` |
| Key env var | `OPENAI_API_KEY` |
| Keys file key | `openai` |
| Auth header | `Authorization: Bearer <key>` |
| Docs | https://platform.openai.com/docs |

**Alternative models:** `o1`, `o3-mini`, `gpt-4-turbo`

---

## Gemini (via OpenAI-compatible endpoint)

| Field | Value |
|---|---|
| Base URL | `https://generativelanguage.googleapis.com/v1beta/openai` |
| Default model | `gemini-2.0-flash` |
| Key env var | `GEMINI_API_KEY` |
| Keys file key | `gemini` |
| Auth header | `Authorization: Bearer <key>` |
| Docs | https://ai.google.dev/gemini-api/docs/openai |

**Alternative models:** `gemini-2.5-pro`, `gemini-1.5-pro`

---

## Adding a New Provider

1. Add an entry to `PROVIDERS` dict in `scripts/model_client.py`:

```python
"myprovider": {
    "base_url": "https://api.myprovider.com/v1",
    "default_model": "model-name",
    "key_env": "MYPROVIDER_API_KEY",
},
```

2. If the provider uses a non-standard auth scheme (not `Authorization: Bearer`), subclass `OpenAICompatClient` and override the headers.

3. Add the provider's key to `~/.claude/dialectic-keys.json`:
```json
{
  "myprovider": "your-api-key"
}
```

4. Re-run `python3 scripts/setup_keys.py --check` to confirm it appears in the council.

---

## Key Storage

API keys are stored in `~/.claude/dialectic-keys.json` (permissions: 600).

Environment variables override file values at runtime. This lets you use system
secrets managers or shell profiles without touching the keys file:

```bash
export DEEPSEEK_API_KEY="sk-..."
export MINIMAX_API_KEY="..."
```

The keys file is never read by Claude directly (it's read by the Python scripts only),
so there's no risk of it being included in conversation context.
