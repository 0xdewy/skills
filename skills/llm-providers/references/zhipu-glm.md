# Zhipu (GLM)

Zhipu AI's GLM family. The BigModel PaaS exposes an OpenAI-compatible v4
endpoint, so the `openai` SDK works directly; the `zhipuai` SDK is available
for native features. (verified 2026-07; both base URLs and the raw-Bearer auth
were confirmed live against a BigModel `id.secret` key, and the thinking +
`reasoning_content` pattern was verified on `glm-4.5-flash`.)

## Get an API key

Mainland: `https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys`
International (z.ai): `https://z.ai/manage-apikey/apikey-list`

Set `ZHIPU_API_KEY` (commonly also `ZAI_API_KEY` for the z.ai stack).

```bash
export ZHIPU_API_KEY="..."
```

> Note: legacy GLM-3 / early v3 endpoints required signing a JWT from your
> `id.secret` pair. The v4 endpoint used here takes the raw API key as a
> Bearer token — no signing.

## Base URL & auth

- Mainland base URL: `https://open.bigmodel.cn/api/paas/v4`
- International base URL (z.ai): `https://api.z.ai/api/paas/v4`
- Auth: `Authorization: Bearer $ZHIPU_API_KEY`
- Endpoint: `POST /chat/completions` (OpenAI-shaped)
- Other surfaces: `POST /embeddings`, `POST /images/generations`,
  `POST /videos/generations` (CogVideoX), web search via
  `tools=[{"type": "web_search", ...}]`.

## SDKs

| Lang | Package | Notes |
|---|---|---|
| Python | `pip install zhipuai` | native SDK |
| TypeScript / Node | `npm install zhipuai` | native SDK |
| Any | `pip install openai` | works at the compat URL above |

## Samples

### curl

```bash
curl https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer $ZHIPU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.6",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python (OpenAI SDK at the compat URL — recommended for portability)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ["ZHIPU_API_KEY"],
)
resp = client.chat.completions.create(
    model="glm-4.6",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Python (native `zhipuai` SDK)

```python
import os
from zhipuai import ZhipuAI

client = ZhipuAI(api_key=os.environ["ZHIPU_API_KEY"])  # base_url defaults to BigModel
resp = client.chat.completions.create(
    model="glm-4.6",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

For z.ai (international), pass `base_url="https://api.z.ai/api/paas/v4"` to
either client constructor.

### Streaming + reasoning

GLM-4.6 (and GLM-4.5-flash in testing) support a thinking mode. **Pass
`thinking` through `extra_body`** — the openai SDK's typed `create()` rejects
it as a direct kwarg. Thinking text streams on `delta.reasoning_content`,
separate from `delta.content`.

```python
stream = client.chat.completions.create(
    model="glm-4.6",
    messages=[{"role": "user", "content": "Solve: 13 * 17 step by step."}],
    extra_body={"thinking": {"type": "enabled"}},
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

For non-streaming, `message.reasoning_content` holds the chain of thought
alongside `message.content`. Thinking requests can be slow — raise the client
`timeout` (e.g. `OpenAI(..., timeout=120.0)`) and budget `max_tokens`
generously, since reasoning tokens come out of the same budget.

### TypeScript

```typescript
import OpenAI from "openai";
const client = new OpenAI({
  baseURL: "https://open.bigmodel.cn/api/paas/v4",
  apiKey: process.env.ZHIPU_API_KEY,
});
const resp = await client.chat.completions.create({
  model: "glm-4.6",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

Verified live on the BigModel `v4` endpoint (2026-07):

- `glm-5.2`, `glm-5.1`, `glm-5` — newest v5 line; verified on the z.ai
  **Coding Plan** endpoint (`https://api.z.ai/api/coding/paas/v4`,
  2026-07-19). All return 200; emit `reasoning_content` like v4.6. No
  `-plus`/`-flash`/`-air` variants on v5 — those return code 1211.
- `glm-4.6` — v4 flagship; supports thinking mode (`reasoning_content`) and tool use
- `glm-4.5-flash` — **free-tier model**; verified working, supports thinking mode
- `glm-4.5`, `glm-4.5-air` — earlier v4.5 line; `-air` is the cheaper, smaller variant
- `glm-4.5v` — vision-language
- `glm-zero-preview` — reasoning preview

Older tier names that **no longer exist** on the current endpoint (they return
code 1211 "model does not exist"): `glm-4`, `glm-4-plus`, `glm-4-air`,
`glm-4-flash`, `glm-4-flashx`, `glm-4-long`. The v5 line has no
`-plus`/`-flash`/`-air` variants either — those ids also return 1211. If a
tutorial references any of them, swap to `glm-4.5-flash` (free),
`glm-4.6` (v4 flagship), or `glm-5.1` (v5, Coding Plan).

Embeddings: `embedding-3`. Image: `cogview-3-plus` / `cogview-4`. Video:
`cogvideox-2` / `cogvideox-flash`.

The model list at `https://docs.z.ai/guides/llm/glm-4.6` (intl.) or
`https://open.bigmodel.cn/dev/api` (mainland) is authoritative — verify before
pinning.

## Gotchas

- **Two base URLs**: BigModel (`open.bigmodel.cn`) for mainland accounts and
  z.ai (`api.z.ai`) for international accounts; the API shape is identical,
  but a key from one does not work on the other.
- **Reasoning field**: GLM-4.6 and GLM-4.5-flash emit `delta.reasoning_content`
  when thinking mode is enabled — same shape as DeepSeek-R1.
- **Thinking param goes through `extra_body`**: the openai SDK's typed
  `chat.completions.create()` rejects `thinking=` as a direct kwarg. Always
  pass `extra_body={"thinking": {"type": "enabled"}}`. Same caveat applies to
  any other Zhipu-only param (`web_search`, etc.).
- **Web search tool**: pass `tools=[{"type": "web_search", "web_search":
  {"enable": true}}]` to ground the answer; results come back in a
  `web_search` field on the response, not as a normal tool call.
- **Function calling**: standard OpenAI `tools`/`tool_calls` shape works.
- **Image inputs**: pass `{"type": "image_url", "image_url": {"url": "..."}`
  inside a `content` array (OpenAI shape) for vision models.
- **Free tier**: `glm-4.5-flash` is free (verified live). Other paid models
  (`glm-4.6`, `glm-4.5-air`) return code 1113 "insufficient balance" until
  you recharge — both BigModel and z.ai share this behavior.
- **Old model ids are gone**: `glm-4`, `glm-4-air`, `glm-4-flash`,
  `glm-4-flashx`, `glm-4-plus`, `glm-4-long` all return code 1211. Use
  `glm-4.5-flash` or `glm-4.6` for new code.
- **Thinking is slow + eats token budget**: thinking tokens count against
  `max_tokens`. With a small budget the model never reaches the answer — set
  `max_tokens` ≥ 1000 and raise the client `timeout` to 120s+ when
  `thinking.enabled`.
