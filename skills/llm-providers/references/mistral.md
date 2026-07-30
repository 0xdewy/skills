# Mistral

Mistral La Plateforme — OpenAI-compatible hosted API for the Mistral,
Codestral, Magistral, Pixtral, and Ministral families. (verified 2026-07)

## Get an API key

`https://console.mistral.ai/api-keys` → set `MISTRAL_API_KEY`. Keys look like
`...` (variable length).

```bash
export MISTRAL_API_KEY="..."
```

## Base URL & auth

- Base URL: `https://api.mistral.ai/v1`
- Auth: `Authorization: Bearer $MISTRAL_API_KEY`
- Endpoint: `POST /chat/completions` (OpenAI-shaped)
- Other surfaces: `POST /embeddings`, `POST /fim/completions` (Fill-in-Middle
  for Codestral), `POST /agents` (Mistral Agents), `POST /files`, chat
  moderation (`POST /moderation/chat`), OCR (`POST /ocr`).

## SDKs

| Lang | Package | Import |
|---|---|---|
| Python | `pip install mistralai` | `from mistralai import Mistral` |
| TypeScript / Node | `npm install @mistralai/mistralai` | `import { Mistral } from "@mistralai/mistralai"` |
| Any | `pip install openai` | works at the compat URL |

## Samples

### curl

```bash
curl https://api.mistral.ai/v1/chat/completions \
  -H "Authorization: Bearer $MISTRAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-large-latest",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python (native SDK)

```python
import os
from mistralai import Mistral

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
resp = client.chat.complete(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Python (OpenAI SDK at the compat URL)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ["MISTRAL_API_KEY"],
)
resp = client.chat.completions.create(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + reasoning (Magistral)

```python
stream = client.chat.completions.create(
    model="magistral-medium-latest",
    messages=[{"role": "user", "content": "Design a rate limiter; explain your reasoning."}],
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
  baseURL: "https://api.mistral.ai/v1",
  apiKey: process.env.MISTRAL_API_KEY,
});
const resp = await client.chat.completions.create({
  model: "mistral-large-latest",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

- `mistral-large-latest` — flagship general/coding
- `mistral-medium-latest`, `mistral-small-latest` — cheaper tiers
- `magistral-medium-latest`, `magistral-small-latest` — reasoning models;
  stream a separate `reasoning` field
- `codestral-latest` — code completion / FIM (use `/fim/completions` for
  prefix/suffix edits)
- `pixtral-large-latest`, `pixtral-12b-2409` — vision + text
- `ministral-8b-latest`, `ministral-3b-latest` — small/edge
- Embeddings: `mistral-embed`
- Models also on HuggingFace (`mistralai/...`) for self-host.

Model list at `https://docs.mistral.ai/getting-started/models/models_overview`
is authoritative.

## Gotchas

- **Suffix `-latest`**: aliases to the latest dated snapshot. Pin a dated id
  (e.g. `mistral-large-2411`) for reproducible behavior in production.
- **Reasoning field**: Magistral returns chain of thought in
  `delta.reasoning` (not `reasoning_content` like DeepSeek/GLM). Read both
  defensively.
- **Guardrail mode**: pass `safe_prompt=true` to force Mistral's built-in
  system-side safety preamble.
- **JSON mode**: `response_format={"type": "json_object"}` works; the model
  must be prompted to produce JSON.
- **Tool calling**: standard OpenAI `tools`/`tool_choice` shape.
- **FIM**: Codestral FIM uses inputs `prompt`, `suffix`, optionally
  `injection_suffix` — different shape from chat completions.
- **Agents**: `POST /v1/agents` lets you attach instructions + tools + docs
  server-side; the agent id is then used as a `model` value.
