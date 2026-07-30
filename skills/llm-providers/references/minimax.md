# MiniMax

MiniMax's hosted LLM API. Two parallel stacks — **mainland China** and
**international** — with separate account registration, separate base URLs,
and separate keys. The international stack is OpenAI-compatible. (verified
2026-07; URLs in this card confirmed live against an international `sk-cp-`
key.)

## Get an API key

- International: `https://platform.minimaxi.com/` (sign in, then
  `Account → API Keys`)
- Mainland: `https://platform.minimax.chat/`

Set `MINIMAX_API_KEY`. The international console also issues a `GroupId`
(`MINIMAX_GROUP_ID`) — only needed for the native `chatcompletion_v2`
endpoint, not for the OpenAI-compat `/chat/completions`.

```bash
export MINIMAX_API_KEY="..."
export MINIMAX_GROUP_ID="..."   # optional — only for native v2 endpoint
```

## Base URL & auth

- International base URL: `https://api.minimaxi.chat/v1`
- Mainland base URL: `https://api.minimax.chat/v1`
- Auth: `Authorization: Bearer $MINIMAX_API_KEY`
- Endpoint (OpenAI-compat): `POST /chat/completions` — no GroupId required.
- Native endpoint (richer fields, mainland-origin API): `POST
  /text/chatcompletion_v2?GroupId=$MINIMAX_GROUP_ID` — returns
  `message.reasoning_content` and `message.reasoning_details` as separate
  fields on reasoning models. Use this when you want structured chain-of-thought.
- Other surfaces: `POST /v1/embeddings`, `POST /v1/video_generation` (Hailuo
  video), `POST /v1/image_generation`, `POST /v1/t2a_v2` (text-to-audio).

## SDKs

| Lang | Package | Notes |
|---|---|---|
| Any | `pip install openai` / `npm install openai` | works at the compat URL |
| Python | `pip install minimax-python` | native SDK, wraps `chatcompletion_v2`, video, audio |
| TypeScript / Node | community only | use `openai` SDK |

## Samples

### curl

```bash
curl https://api.minimaxi.chat/v1/chat/completions \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-M2",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python (OpenAI SDK at the compat URL — recommended)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.minimaxi.chat/v1",
    api_key=os.environ["MINIMAX_API_KEY"],
)
resp = client.chat.completions.create(
    model="MiniMax-M2",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + reasoning

Two paths — pick based on how much structure you need.

**OpenAI-compat (`/chat/completions`, no GroupId):** reasoning text appears as
`<think>...</think>` tags **inside `content`**. Strip them client-side; the
usage object reports `completion_tokens_details.reasoning_tokens` separately.

```python
import re
stream = client.chat.completions.create(
    model="MiniMax-M2",
    messages=[{"role": "user", "content": "Prove sqrt(2) is irrational."}],
    stream=True,
)
buf = []
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        buf.append(delta.content)
        print(delta.content, end="", flush=True)
full = "".join(buf)
answer_only = re.sub(r"<think>.*?</think>\s*", "", full, flags=re.DOTALL).strip()
# usage.reported reasoning tokens (non-streaming) on resp.usage.completion_tokens_details.reasoning_tokens
```

**Native v2 (`/text/chatcompletion_v2?GroupId=...`):** returns
`message.reasoning_content` and `message.reasoning_details` as separate
fields. Easier to consume when reasoning structure matters:

```python
import os, httpx
r = httpx.post(
    "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
    params={"GroupId": os.environ["MINIMAX_GROUP_ID"]},
    headers={"Authorization": f"Bearer {os.environ['MINIMAX_API_KEY']}"},
    json={
        "model": "MiniMax-M2",
        "messages": [{"role": "user", "content": "Prove sqrt(2) is irrational."}],
    },
    timeout=60,
)
data = r.json()
msg = data["choices"][0]["message"]
print(f"[think] {msg.get('reasoning_content', '')}")
print(f"[answer] {msg['content']}")
```

### TypeScript

```typescript
import OpenAI from "openai";
const client = new OpenAI({
  baseURL: "https://api.minimaxi.chat/v1",
  apiKey: process.env.MINIMAX_API_KEY,
});
const resp = await client.chat.completions.create({
  model: "MiniMax-M2",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

- `MiniMax-M2` — flagship reasoning/general model (international name)
- `MiniMax-M1` — MoE reasoning model with separate `reasoning_content`
- `MiniMax-Text-01` — 1M-context model; set `model="mini-max-text-01"` on
  older SDK paths
- `abab6.5s-chat`, `abab6.5-chat`, `abab6-chat` — legacy chat tiers
- `speech-01-240228` / `speech-02-hd` — TTS
- `video-01` / `video-01-live2d` — Hailuo video generation
- `voice-clone-tasks` — voice cloning
- `embo01` — embeddings

The model list at `https://platform.minimaxi.com/document/Models` is
authoritative. Mainland platform naming sometimes lowercases/dashes — verify.

## Gotchas

- **Two stacks, two keys**: international (`api.minimaxi.chat`) and mainland
  (`api.minimax.chat`) keys are not interchangeable. Use the international
  stack for non-China billing. (Verified live: the `sk-cp-...` international
  token is rejected on `api.minimax.chat` and also on the older
  `api.minimaxi.com` host — only `api.minimaxi.chat` accepts it.)
- **GroupId**: required on the native `chatcompletion_v2` / `chatcompletion_pro`
  endpoints (`?GroupId=...`). The OpenAI-compat `/chat/completions` path does
  **not** need it.
- **Reasoning field differs by endpoint**: the OpenAI-compat endpoint keeps
  chain of thought as `<think>...</think>` inside `content` (strip client-side;
  `usage.completion_tokens_details.reasoning_tokens` reports the count). The
  native v2 endpoint returns it in `message.reasoning_content` and
  `message.reasoning_details`. Pick the right endpoint for your parsing.
- **Long context**: MiniMax-Text-01 supports up to 1M tokens; set the
  `max_tokens` budget high and use streaming — the full response can be slow.
- **Pricing**: billed in CNY on the mainland stack and USD on the international
  stack; token pricing differs. Check the dashboard before relying on quoted
  numbers.
- **Region availability**: Hailuo video generation has tighter region/queue
  rules than the chat API; if a video request 403s, check the dashboard
  allowlist rather than retrying.
- **JWT signing is deprecated**: older MiniMax docs describe signing a JWT from
  `(api_key, group_id)`. Current stacks take the raw `sk-...` key as Bearer
  directly — do not mint a JWT, it now produces a 1004 "Please carry the API
  secret key in 'Authorization'" error.
