# Moonshot (Kimi)

Moonshot AI's Kimi/Moonshot hosted API — OpenAI-compatible. Long-context
(Kimi) is the headline feature. (verified 2026-07)

## Get an API key

- International: `https://platform.moonshot.ai/`
- Mainland: `https://platform.moonshot.cn/console/api-keys`

Set `MOONSHOT_API_KEY`. Keys look like `sk-...`.

```bash
export MOONSHOT_API_KEY="sk-..."
```

## Base URL & auth

- International base URL: `https://api.moonshot.ai/v1`
- Mainland base URL: `https://api.moonshot.cn/v1`
- Auth: `Authorization: Bearer $MOONSHOT_API_KEY`
- Endpoint: `POST /chat/completions` (OpenAI-shaped)
- Other surfaces: `POST /v1/files` (upload up to 100 MB of context for Kimi),
  `POST /v1/embeddings`, `POST /v1/batches`, `POST /v1/tool_calls/fundraise`
  (rare), rerank.

## SDKs

| Lang | Package | Notes |
|---|---|---|
| Any | `pip install openai` / `npm install openai` | works at the compat URL |
| Python | `pip install moonshot-python` (community) | thin wrapper |

There is no first-party Python/TS SDK that's required — the OpenAI SDK at the
Moonshot base URL is the recommended client.

## Samples

### curl

```bash
curl https://api.moonshot.ai/v1/chat/completions \
  -H "Authorization: Bearer $MOONSHOT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshot-v1-32k",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.moonshot.ai/v1",
    api_key=os.environ["MOONSHOT_API_KEY"],
)
resp = client.chat.completions.create(
    model="moonshot-v1-32k",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### File-grounded Kimi (long context)

Upload a file, then reference it via `role: "system"` content:

```python
upload = client.files.create(
    file=open("spec.pdf", "rb"),
    purpose="file-extract",
)
content = (
    f"fileid://{upload.id}\n\n"
    "Summarize the document above in 5 bullets."
)
resp = client.chat.completions.create(
    model="moonshot-v1-128k",
    messages=[{"role": "system", "content": content},
              {"role": "user", "content": "Go."}],
)
print(resp.choices[0].message.content)
```

### Streaming + reasoning (Kimi K1.5 / K2 thinking)

Kimi K1.5 and K2 thinking variants stream a `reasoning_content` field on the
delta — same shape as DeepSeek-R1 and Qwen3:

```python
stream = client.chat.completions.create(
    model="kimi-thinking-preview",
    messages=[{"role": "user", "content": "Prove sqrt(2) is irrational."}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta
    rc = getattr(delta, "reasoning_content", None)
    if rc:
        print(f"[think] {rc}", end="", flush=True)
    elif delta.content:
        print(delta.content, end="", flush=True)
```

### TypeScript

```typescript
import OpenAI from "openai";
const client = new OpenAI({
  baseURL: "https://api.moonshot.ai/v1",
  apiKey: process.env.MOONSHOT_API_KEY,
});
const resp = await client.chat.completions.create({
  model: "moonshot-v1-32k",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

- `moonshot-v1-8k`, `moonshot-v1-32k`, `moonshot-v1-128k` — Moonshot v1 at
  three context windows; pick the smallest window that fits
- `kimi-k2-0905-preview` — Kimi K2 preview, agentic + tool use focus
- `kimi-thinking-preview` — Kimi reasoning, emits `reasoning_content`
- `moonshot-v1-32k-context...` aliases exist — verify on the model page
- Embeddings: `text-embedding-v1`

Model list at `https://platform.moonshot.ai/docs/intro` (intl.) or
`https://platform.moonshot.cn/docs` (mainland) is authoritative.

## Gotchas

- **Two base URLs**: `api.moonshot.ai` (intl.) vs `api.moonshot.cn` (mainland).
  Keys are not interchangeable.
- **Pick the smallest context window**: Moonshot charges per token but also
  per-window for some plans; `moonshot-v1-8k` is cheaper than `-128k`. If you
  don't need 128k, don't request it.
- **File grounding**: use the Files API (`purpose="file-extract"`) and pass
  `fileid://<id>` in a system message; this is Moonshot's first-class RAG
  pattern. Don't paste long documents into the user message if a file id will
  do.
- **Reasoning field**: Kimi thinking emits `delta.reasoning_content` (same as
  DeepSeek-R1 / Qwen3 / GLM-4.6).
- **Tool calling**: standard OpenAI `tools`/`tool_calls` shape works.
- **Strict output mode**: pass `response_format={"type": "json_object"}` like
  OpenAI; prompt the model to produce JSON.
