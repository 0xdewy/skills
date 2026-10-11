---
name: llm-providers
description: >-
  Developer reference for connecting to OpenAI, Anthropic, Gemini, DeepSeek,
  GLM, MiniMax, MiMo, Mistral, xAI, Qwen, Kimi, Cohere, OpenRouter, Together,
  and Groq APIs, covering auth, endpoints, SDKs, models, and provider gotchas.
  Only use when explicitly requested.
disable-model-invocation: true
---

# LLM Providers

Wire an application to a hosted LLM API. Each provider has a card in
`references/<provider>.md`: where to get a key, the env var name, REST base
URL, auth header, OpenAI compatibility, official Python and TypeScript SDKs,
working curl, Python, and TS samples, current model names, and gotchas.

## Workflow

1. Identify provider and language. Run
   `scripts/search_refs.py --limit 4 "<provider or feature terms>"` and open
   only the matching card. `references/concepts.md` covers cross-provider
   topics: OpenAI-compatible endpoints, streaming, retries, tool calling, and
   the env-var convention.
2. Take base URL, auth header, env var, and model string from the card, never
   from memory. If the card is stale or lacks the model, say so and check the
   provider docs linked in the card.
3. Copy the card's sample for the target language. Prefer the `openai` SDK
   against a compatible base URL unless the user wants the vendor SDK.
4. Read the key from the card's env var or a secret store. Never hardcode,
   echo, log, or commit a key, and never accept one pasted into the prompt.
5. Surface the card's gotchas (region limits, special headers, context
   limits, multimodal caveats) before the user hits them.
6. Before claiming a snippet runs, confirm the SDK imports
   (`python -c "import openai"` or the card's package).

This skill targets official hosted APIs. It is not for bypassing rate limits,
region locks, or auth.
