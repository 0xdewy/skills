# Cohere

Cohere's hosted API for the Command family, plus embeddings, rerank, and
classify. Native API is `/v2/chat`; an OpenAI-compat shim exists for chat-only
use. (verified 2026-07)

## Get an API key

`https://dashboard.cohere.com/api-keys` → set `COHERE_API_KEY` (or
`CO_API_KEY`). Keys look like `...` (variable length). Production keys have a
scope (chat, embed, rerank, fine-tune) — pick the smallest scope that fits.

```bash
export COHERE_API_KEY="..."
```

## Base URL & auth

- Base URL: `https://api.cohere.com/v2` (native v2 chat)
- OpenAI-compat base URL: `https://api.cohere.ai/compatibility/v1`
- Auth: `Authorization: Bearer $COHERE_API_KEY`
- Native endpoint: `POST /v2/chat` (preferred for new code)
- Legacy endpoint: `POST /v1/chat` (deprecated)
- Other surfaces: `POST /v2/embed`, `POST /v1/rerank`, `POST /v1/classify`,
  `POST /v1/summarize`, `POST /v2/finetuned/...`.

## SDKs

| Lang | Package | Import |
|---|---|---|
| Python | `pip install cohere` | `import cohere` |
| TypeScript / Node | `npm install cohere-ai` | `import { CohereClient } from "cohere-ai"` |
| Any | `pip install openai` | works at the compat URL (chat only) |

## Samples

### curl (native v2)

```bash
curl https://api.cohere.com/v2/chat \
  -H "Authorization: Bearer $COHERE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "command-a-03-2025",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python (native SDK)

```python
import os
import cohere

client = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])
resp = client.chat(
    model="command-a-03-2025",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.message.content[0].text)
```

### Python (OpenAI SDK at the compat URL — chat only)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.cohere.ai/compatibility/v1",
    api_key=os.environ["COHERE_API_KEY"],
)
resp = client.chat.completions.create(
    model="command-a-03-2025",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + tool use (Python)

```python
stream = client.chat_stream(
    model="command-a-03-2025",
    messages=[{"role": "user", "content": "What's the weather in Kyoto?"}],
    tools=[{
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
    }],
)
for event in stream:
    if event.type == "content-delta":
        print(event.delta.message.content.text, end="", flush=True)
    elif event.type == "tool-call":
        args = event.tool_call.function.arguments
        print(f"\n[tool call] {args}")
```

### Embeddings + rerank (Python)

```python
emb = client.embed(
    texts=["hello", "world"],
    model="embed-v4.0",
    input_type="search_document",
    embedding_types=["float"],
)
# Then for ranking a candidate set against a query:
ranked = client.rerank(
    model="rerank-v3.5",
    query="capital of Japan",
    documents=["Tokyo", "Kyoto", "Osaka", "Sapporo"],
    top_n=2,
)
```

### TypeScript

```typescript
import { CohereClient } from "cohere-ai";
const client = new CohereClient({ token: process.env.COHERE_API_KEY });
const resp = await client.chat({
  model: "command-a-03-2025",
  message: "Say hello in one short sentence.",
});
console.log((resp.text ?? "").toString());
```

## Current models

- `command-a-03-2025` — flagship; strong tool use and RAG
- `command-r-08-2024`, `command-r-plus-08-2024` — earlier Command R family
- `command-r7b-12-2024` — small/edge
- `command` (alias) — points to a recent default
- Embeddings: `embed-v4.0` (multimodal), `embed-english-v3.0`,
  `embed-multilingual-v3.0`
- Rerank: `rerank-v3.5`, `rerank-multilingual-v3.0`
- Classification: `classify-finetune-...`

Model list at `https://docs.cohere.com/docs/models` is authoritative.

## Gotchas

- **v1 vs v2 chat**: v2 (`/v2/chat`, `client.chat`) is the current API and
  uses OpenAI-shaped `messages`. v1 (`/v1/chat`, `client.chat` with
  `message=` string) is deprecated and will be sunset. Don't write new code
  against v1.
- **Compat shim is chat-only**: embeddings, rerank, and classify must go
  through the native SDK. The compat endpoint won't proxy them.
- **`input_type`**: embeddings require `input_type` of
  `search_document` | `search_query` | `classification_document` |
  `classification_query` | `clustering` — wrong value degrades retrieval.
- **Tool calls**: returned as events in streaming, and on
  `message.tool_calls` in non-streaming. Tool results are sent back as a
  `role: "tool"` message with `tool_call_id`.
- **Connectors / RAG**: pass `connectors=[{"id": "web-search"}]` to ground
  chat in live web search; citations appear in `message.citations`.
- **Truncation**: long prompts are silently truncated unless you pass
  `truncate="END" | "START" | "OFF"`. For RAG use `END`.
