---
name: llm-providers
description: >-
  Developer reference for connecting to OpenAI, Anthropic, Gemini, DeepSeek,
  GLM, MiniMax, MiMo, Mistral, xAI, Qwen, Kimi, Cohere, OpenRouter, Together,
  and Groq APIs, covering auth, endpoints, SDKs, models, and provider gotchas.
  Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: skill-lab
  version: 1.0.0
  category: integration
  tags:
    - llm
    - api
    - openai
    - anthropic
    - gemini
    - deepseek
    - glm
    - minimax
    - sdk
---

# LLM Providers

Wire an application up to a hosted LLM API. For each provider this skill keeps
a reference card with: where to get a key, the canonical env-var name, REST
base URL, auth header, OpenAI-compatibility, official Python/TypeScript SDK
packages, working `curl`/Python/TS samples, current model names, and known
gotchas.

## Source Discipline

Run `scripts/search_refs.py --limit 4 "<provider or feature terms>"` first, then
open only the matching reference file(s). Do not guess base URLs, auth header
names, or model strings — model lineups and endpoints change. If freshness
matters or the local card is missing the model you need, browse the provider's
official docs (linked in each card) before writing code.

## Routing

- Already know the provider? Open `references/<provider>.md` directly.
- Comparing providers, picking a model, or explaining shared patterns
  (OpenAI-compat, streaming, retries, env-var convention, tool calling):
  `references/concepts.md`.
- Need the canonical `OPENAI_API_KEY`-style env var for a provider:
  `references/concepts.md` → "Env-var convention".
- Want one SDK against many providers: `references/openrouter.md` or
  `references/concepts.md` → "OpenAI-compatible endpoints".
- Unsure which file matches: `references/index.md` or run `search_refs.py`.

## Workflow

1. Identify the provider and language (Python/TypeScript/curl/REST).
2. Load the matching `references/<provider>.md`. Confirm the base URL and auth
   header from the card, not memory.
3. Use the env-var named in the card. Never hardcode a key in source. Never
   accept a key typed into a prompt — read it from the environment or a secret
   store the user owns.
4. Copy the card's sample for the target language, swap in the user's model
   name (cards list current defaults — verify if the request is older than the
   card's "verified" date).
5. If the provider is OpenAI-compatible, prefer the `openai` SDK pointed at the
   compat base URL over a vendor SDK unless the user asked for the native SDK.
6. Surface gotchas from the card (region restrictions, special headers, context
   limits, image/multimodal caveats) before the user hits them.

## Safety

- Treat API keys as user-owned secrets. Read from env vars or a secret manager.
  Never echo, log, or commit a key.
- Do not invent endpoints, model names, or auth schemes. If a card is stale,
  say so and check the provider's docs.
- This skill integrates with official, hosted APIs. It is not for bypassing
  rate limits, region locks, or auth.

## Verification

For any code produced from this skill:

1. The provider card's base URL and auth header match the sample.
2. The model string exists in the card's model list (or you flagged the
   divergence).
3. The sample reads the key from the documented env var, not a literal.
4. `python -c "import openai"` (or the card's SDK) succeeds before claiming the
   snippet runs.
