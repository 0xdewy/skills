# xAI (Grok)

xAI's hosted API for the Grok family — OpenAI-compatible, drop-in for the
`openai` SDK. (verified 2026-07)

## Get an API key

`https://console.x.ai/` → set `XAI_API_KEY`. Keys look like `xai-...`.

```bash
export XAI_API_KEY="xai-..."
```

## Base URL & auth

- Base URL: `https://api.x.ai/v1`
- Auth: `Authorization: Bearer $XAI_API_KEY`
- Endpoint: `POST /chat/completions` (OpenAI-shaped)
- Other surfaces: `POST /embeddings` (`v1/embeddings`), `POST /images/generations`,
  Live Search via `search_parameters`.

## SDKs

| Lang | Package | Notes |
|---|---|---|
| Any | `pip install openai` / `npm install openai` | works at the compat URL |
| Python | `pip install xai-sdk` | research SDK for Grok-heavy apps |
| TypeScript / Node | community only | use `openai` SDK |

## Samples

### curl

```bash
curl https://api.x.ai/v1/chat/completions \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-4",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.x.ai/v1",
    api_key=os.environ["XAI_API_KEY"],
)
resp = client.chat.completions.create(
    model="grok-4",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + reasoning (Grok with thinking)

Pass `reasoning_effort` to enable chain-of-thought on supporting models; the
chain-of-thought text streams in `delta.reasoning`:

```python
stream = client.chat.completions.create(
    model="grok-4",
    messages=[{"role": "user", "content": "Compute 23*17 mentally; explain."}],
    reasoning_effort="low",   # "low" | "high"
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta
    rc = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
    if rc:
        print(f"[think] {rc}", end="", flush=True)
    elif delta.content:
        print(delta.content, end="", flush=True)
```

### TypeScript

```typescript
import OpenAI from "openai";
const client = new OpenAI({
  baseURL: "https://api.x.ai/v1",
  apiKey: process.env.XAI_API_KEY,
});
const resp = await client.chat.completions.create({
  model: "grok-4",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

- `grok-4` — flagship; supports `reasoning_effort`, tool use, Live Search
- `grok-4-fast` — lower-latency variant
- `grok-3`, `grok-3-mini` — previous flagship line, still available
- `grok-3-fast`, `grok-3-mini-fast` — fast tier
- `grok-2-vision-1212` — vision-capable
- `grok-code-fast-1` — coding-focused fast tier
- Embeddings: `v1/embeddings` model `text-embedding`

Model list at `https://docs.x.ai/docs/models` is authoritative.

## Gotchas

- **OpenAI-compat is the primary surface**: the `openai` SDK is the
  recommended client; there is no need for a separate Grok SDK for chat.
- **`reasoning_effort`**: Grok's parameter mirrors OpenAI's. Setting it
  enables thinking mode and bills reasoning tokens separately.
- **Live Search**: pass
  `search_parameters={"mode": "auto" | "on", "sources": [...]}` to ground
  answers in real web/X results. Results are returned in
  `choices[0].message.search_results`. There is a per-source cost.
- **Image inputs**: pass `{"type": "image_url", "image_url": {"url": "..."}}`
  inside a `content` array for vision-capable Grok variants.
- **Image generation**: `POST /v1/images/generations` is OpenAI-DALL·E shaped.
- **Pricing**: Grok-4 is usage-tier gated; check console for current rate
  card before bulk use.
