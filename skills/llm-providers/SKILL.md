---
name: llm-providers
description: >-
  Developer reference for connecting to OpenAI, Anthropic, Gemini, DeepSeek,
  GLM, MiniMax, MiMo, Mistral, xAI, Qwen, Kimi, Cohere, OpenRouter, Together,
  and Groq APIs: env vars, base URLs, auth, SDKs, and gotchas.
  Only use when explicitly requested.
disable-model-invocation: true
---

# LLM Providers

Wire an application to a hosted LLM API.

1. Look up the provider in `references/providers.md`: env var, base URL, auth
   header, OpenAI-compat URL, SDK packages, models page, gotchas.
2. Get model IDs at task time from the provider's models page or
   `GET {base_url}/models`. If you could not check, say the ID is unverified.
3. Default to the `openai` SDK at the compat base URL. Use the vendor SDK for
   vendor-only features (Anthropic native, Gemini native, Cohere embed/rerank).
4. Read the key from the env var or a secret store. Never hardcode, echo, log,
   or commit a key, and never accept one pasted into the prompt.
5. Raise the provider's gotchas before the user hits them.

```python
import os
from openai import OpenAI

client = OpenAI(base_url="https://api.deepseek.com/v1",
                api_key=os.environ["DEEPSEEK_API_KEY"])
resp = client.chat.completions.create(
    model="<id from the models page, checked today>",
    messages=[{"role": "user", "content": "ping"}],
)
```

## Where compat providers diverge

- Reasoning text arrives in `delta.reasoning_content` (DeepSeek, GLM, Qwen,
  Kimi), `delta.reasoning` (OpenAI, Mistral), or `<think>` tags inside
  `content` (MiniMax compat). Read the field the provider uses.
- Vendor-only params (GLM `thinking`, Qwen `enable_thinking`, OpenRouter
  `provider`) go in `extra_body`; the openai SDK rejects them as kwargs.
- Facts were verified 2026-07. If a call fails on URL or auth, check the
  provider docs before assuming the code is wrong.

This skill targets official hosted APIs. It is not for bypassing rate limits,
region locks, or auth.
