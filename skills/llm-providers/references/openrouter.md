# OpenRouter

OpenRouter is a single OpenAI-compatible gateway to hundreds of models from
OpenAI, Anthropic, Google, Meta, Mistral, xAI, DeepSeek, Qwen, and many
others. One key, one SDK, one bill. (verified 2026-07)

## Get an API key

`https://openrouter.ai/keys` → set `OPENROUTER_API_KEY`. Keys look like
`sk-or-v1-...`. Add credits on the dashboard; pay-as-you-go, no per-provider
signup.

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

## Base URL & auth

- Base URL: `https://openrouter.ai/api/v1`
- Auth: `Authorization: Bearer $OPENROUTER_API_KEY`
- Endpoint: `POST /chat/completions` (OpenAI-shaped) — and
  `POST /completions`, `POST /embeddings`, plus `/images/generations`.
- Optional attribution headers (no auth function, but useful for the
  OpenRouter leaderboard):
  - `HTTP-Referer: https://your-app.example`
  - `X-Title: Your App Name`

## SDKs

| Lang | Package | Notes |
|---|---|---|
| Any | `pip install openai` / `npm install openai` | works at the compat URL |
| Python | `pip install openrouter` (community) | thin |
| TypeScript / Node | community only | use `openai` SDK |

## Samples

### curl

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "HTTP-Referer: https://example.com" \
  -H "X-Title: Demo App" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
resp = client.chat.completions.create(
    model="anthropic/claude-sonnet-4.5",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Routing — fallbacks, caching, and provider choice

OpenRouter's differentiator is the `provider` routing block:

```python
resp = client.chat.completions.create(
    model="anthropic/claude-sonnet-4.5",
    messages=[...],
    extra_body={
        "provider": {
            "order": ["Anthropic", "AWS Bedrock"],          # try in this order
            "allow_fallbacks": True,
            "require_parameters": True,
        },
        "fallbacks": ["openai/gpt-4.1", "google/gemini-2.5-pro"],
        "transforms": ["middle-out"],                       # auto-compress long context
        "max_tokens": 1024,
    },
)
```

- `order`/`allow_fallbacks` — try one provider backend, then another.
- `fallbacks` — try a different *model* if the primary is down.
- `transforms` — `middle-out` compresses long context to fit.
- `usage`/`cost` are returned on every response.

### TypeScript

```typescript
import OpenAI from "openai";
const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://example.com",
    "X-Title": "Demo App",
  },
});
const resp = await client.chat.completions.create({
  model: "openai/gpt-4.1",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Model strings

The model id is always `provider/model-name`. Examples (verify at
`https://openrouter.ai/models` for the live list):

- `openai/gpt-4.1`, `openai/gpt-4o`, `openai/gpt-5` (when available)
- `anthropic/claude-sonnet-4.5`, `anthropic/claude-opus-4.1`,
  `anthropic/claude-haiku-4.5`
- `google/gemini-2.5-pro`, `google/gemini-2.5-flash`,
  `google/gemini-3-pro` (when available)
- `x-ai/grok-4`, `x-ai/grok-4-fast`
- `deepseek/deepseek-chat`, `deepseek/deepseek-r1`
- `qwen/qwen3-235b-a22b`, `qwen/qwen-2.5-72b-instruct`
- `mistralai/mistral-large-2411`, `mistralai/codestral-2501`
- `meta-llama/llama-3.3-70b-instruct`
- `moonshotai/kimi-k2`
- `zhipuai/glm-4.6`

Some ids carry a `:free` suffix (`meta-llama/llama-3.3-70b-instruct:free`)
for the free-tier endpoint with stricter rate limits.

## Gotchas

- **Routing adds latency**: when `allow_fallbacks=True`, the first failed
  request still incurs connection time before retrying on another provider.
  For latency-sensitive paths pin a single `provider.order`.
- **Pricing is per-provider, not a markup floor**: OpenRouter shows input +
  output $/M-token for each model on the model page. Cheapest path can be
  to call the provider directly; OpenRouter's value is one key + fallback.
- **`reasoning` field**: for reasoning models OpenRouter passes the upstream
  `reasoning` / `reasoning_content` through on the delta; read both
  defensively.
- **`provider` block goes in `extra_body`** on the openai SDK because it's
  OpenRouter-specific schema.
- **Free tier (`:free`)**: rate-limited and may route to a community cache;
  don't use for production. Fine for smoke tests.
- **Credits**: OpenRouter prepay is shared across providers. When your
  balance runs out mid-stream, the stream ends with a 402.
- **Anthropic/Gemini via OpenRouter** is OpenAI-shaped (the OpenRouter
  normalizer); this is a convenient way to skip Anthropic's `x-api-key`
  + Messages-specific shape if you only need chat.
