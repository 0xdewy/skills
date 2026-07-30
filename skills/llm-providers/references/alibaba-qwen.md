# Alibaba Qwen (DashScope)

Alibaba Cloud's DashScope hosts the Qwen family. Two surfaces — the **native
DashScope** API and an **OpenAI-compatible mode** at a different base URL.
(verified 2026-07)

## Get an API key

`https://bailian.console.aliyun.com/` (Model Studio / DashScope) →
`Workspace → API-KEY` → set `DASHSCOPE_API_KEY`. Keys look like `sk-...`.

```bash
export DASHSCOPE_API_KEY="sk-..."
```

## Base URL & auth

- **OpenAI-compat base URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
  ← recommended for code that should be portable across providers.
- **Native base URL**: `https://dashscope.aliyuncs.com/api/v1`
- Auth: `Authorization: Bearer $DASHSCOPE_API_KEY`
- Compat endpoint: `POST /chat/completions` (OpenAI-shaped)
- Other surfaces (native): `POST /services/aigc/text-generation/generation`,
  `POST /services/embeddings/multimodal-embedding/multimodal-embedding`,
  `POST /services/aigc/text-generation/generation` for Qwen-Long (file + msg),
  image generation, Rerank, OCR.

## SDKs

| Lang | Package | Notes |
|---|---|---|
| Any | `pip install openai` | works at the compat URL |
| Python | `pip install dashscope` | native SDK |
| TypeScript / Node | `npm install dashscope` | community / thin |

## Samples

### curl (OpenAI-compat mode — recommended)

```bash
curl https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-plus",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python (OpenAI SDK at the compat URL)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ["DASHSCOPE_API_KEY"],
)
resp = client.chat.completions.create(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Python (native `dashscope` SDK)

```python
import os
import dashscope
dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]

resp = dashscope.Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.output.choices[0].message.content)
```

### Streaming + reasoning (Qwen3 thinking)

Qwen3 supports a `enable_thinking` flag (default `True` on thinking-capable
models). On the compat endpoint set
`extra_body={"enable_thinking": True}` and stream:

```python
stream = client.chat.completions.create(
    model="qwen3-235b-a22b",
    messages=[{"role": "user", "content": "Prove sqrt(2) is irrational."}],
    extra_body={"enable_thinking": True, "stream": True},
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
  baseURL: "https://dashscope.aliyuncs.com/compatible-mode/v1",
  apiKey: process.env.DASHSCOPE_API_KEY,
});
const resp = await client.chat.completions.create({
  model: "qwen-plus",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

- `qwen3-235b-a22b`, `qwen3-32b`, `qwen3-30b-a3b`, `qwen3-14b`, `qwen3-8b`,
  `qwen3-4b`, `qwen3-1.7b`, `qwen3-0.6b` — Qwen3 family, MoE + dense, all
  support `enable_thinking`
- `qwen-max`, `qwen-plus`, `qwen-turbo` — older alias tiers (route to a
  specific backend model)
- `qwen-coder-plus`, `qwen-coder-plus-bash` — coding
- `qwen-long` — long-context (up to 10M chars with file inputs)
- `qwen-vl-max`, `qwen-vl-plus`, `qwen2.5-vl-72b-instruct` — vision-language
- `qwen-math-plus`, `qwen2.5-math-72b-instruct` — math
- Embeddings: `text-embedding-v3`, `text-embedding-v4`
- Rerank: `gte-rerank`
- Image: `flux-dev`, `wanx2.1-t2i-turbo`

Model list at
`https://help.aliyun.com/zh/model-studio/getting-started/models` is
authoritative.

## Gotchas

- **Two base URLs, same key**: the compat endpoint and the native endpoint
  accept the same `DASHSCOPE_API_KEY`. Don't pass `/api/v1` to the compat
  client or vice versa.
- **`extra_body` is the escape hatch**: Qwen-only params (`enable_thinking`,
  `result_format`, `seed`, `top_p` gating) go through `extra_body` on the
  openai SDK because they aren't part of the OpenAI schema.
- **Thinking field**: Qwen3 emits `delta.reasoning_content` when
  `enable_thinking=True` — same convention as DeepSeek-R1.
- **Region**: DashScope serves both international and mainland accounts from
  the same hostname; an Alibaba Cloud China account is required to obtain a
  key. International users can access Qwen via OpenRouter, Together, or
  `modelscope.cn`.
- **Qwen-Long**: pass uploaded file ids in `messages` (role `system` or
  `user` with `content` referencing `fileid://...`); the file API is at
  `POST /api/v1/uploads`.
- **Function calling**: standard OpenAI `tools`/`tool_calls` on the compat
  endpoint.
