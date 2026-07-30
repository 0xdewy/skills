# OpenAI

The reference for the OpenAI-shaped Chat Completions API that most other cards
imitate. (verified 2026-07)

## Get an API key

`https://platform.openai.com/api-keys` → set `OPENAI_API_KEY` in the
environment. Keys look like `sk-...` (or `sk-proj-...`).

```bash
export OPENAI_API_KEY="sk-..."
```

## Base URL & auth

- Base URL: `https://api.openai.com/v1`
- Auth header: `Authorization: Bearer $OPENAI_API_KEY`
- Two first-party surfaces:
  - **Chat Completions** — `POST /v1/chat/completions` (universal, supported by
    every OpenAI-compat provider).
  - **Responses API** — `POST /v1/responses` (newer; first-class tool use,
    stateful conversations, web search / file search built in). Prefer it for
    new OpenAI-only apps; prefer Chat Completions when you want portability.

## SDKs

| Lang | Package | Import |
|---|---|---|
| Python | `pip install openai` | `from openai import OpenAI` |
| TypeScript / Node | `npm install openai` | `import OpenAI from "openai"` |

The SDKs auto-pick `OPENAI_API_KEY` from env when constructed with no args.

## Samples

### curl

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python

```python
import os
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY, timeout=60, max_retries=2 by default
resp = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + tool call (Python)

```python
import json
from openai import OpenAI

client = OpenAI()
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]

stream = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "What's the weather in Kyoto?"}],
    tools=tools,
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="", flush=True)
```

### TypeScript

```typescript
import OpenAI from "openai";
const client = new OpenAI(); // reads OPENAI_API_KEY

const resp = await client.chat.completions.create({
  model: "gpt-4.1",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models (verify on platform before shipping)

Flagship / general-purpose:
- `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano` — main Chat Completions workhorses
- `gpt-4o`, `gpt-4o-mini`, `gpt-4o-fast` — multimodal (text + image), still common
- `gpt-5`, `gpt-5-mini`, `gpt-5-nano` — latest flagship family (use when
  available in your org; verify name)

Reasoning:
- `o3`, `o3-mini`, `o4-mini` — `reasoning_effort` parameter controls thinking
  budget; reasoning tokens bill separately.

Audio / image / embeddings (different endpoints):
- `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `tts-1`, `tts-1-hd`, `dall-e-3`,
  `gpt-image-1`, `text-embedding-3-small`, `text-embedding-3-large`

The model list at `https://platform.openai.com/docs/models` is authoritative.

## Gotchas

- Chat Completions is the **portable** surface — the same SDK and code path
  works against DeepSeek, GLM, MiniMax, Mistral, xAI, Qwen, Moonshot, Together,
  Groq, and OpenRouter. Reach for the Responses API only for OpenAI-only work.
- Reasoning models (`o3`, `o4-mini`) reject some parameters (`temperature`,
  `top_p`, system messages — pass instructions via the first user message).
- Streaming reasoning: deltas may arrive in `delta.reasoning` rather than
  `delta.content` depending on the model. Don't conflate them.
- Images can be passed either as a URL or as a base64 data URI in the message
  `content` array. Always specify `detail: low|high|auto`.
- Rate limits are per-organization, tiered by spend history. Check the usage
  page when you see 429s — they may be TPM rather than RPM.
