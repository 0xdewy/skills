# Together AI

Together AI hosts open-weight models (Llama, Qwen, DeepSeek, Mistral, DBRX,
etc.) behind an OpenAI-compatible API, plus hosted fine-tuning. (verified
2026-07)

## Get an API key

`https://api.together.ai/settings/api-keys` → set `TOGETHER_API_KEY`. Keys
look like `...` (hex-ish).

```bash
export TOGETHER_API_KEY="..."
```

## Base URL & auth

- Base URL: `https://api.together.xyz/v1`
- Auth: `Authorization: Bearer $TOGETHER_API_KEY`
- Endpoint: `POST /chat/completions` (OpenAI-shaped)
- Other surfaces: `POST /completions` (raw), `POST /embeddings`,
  `POST /images/generations`, `POST /fine-tunes`, `POST /rerank`,
  `POST /code/completions` (code FIM).

## SDKs

| Lang | Package | Import |
|---|---|---|
| Python | `pip install together` | `from together import Together` |
| TypeScript / Node | `npm install together-ai` | `import { Together } from "together-ai"` |
| Any | `pip install openai` | works at the compat URL |

## Samples

### curl

```bash
curl https://api.together.xyz/v1/chat/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python (native SDK)

```python
import os
from together import Together

client = Together(api_key=os.environ["TOGETHER_API_KEY"])
resp = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Python (OpenAI SDK at the compat URL)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=os.environ["TOGETHER_API_KEY"],
)
resp = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + reasoning (DeepSeek-R1 on Together)

```python
stream = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
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
  baseURL: "https://api.together.xyz/v1",
  apiKey: process.env.TOGETHER_API_KEY,
});
const resp = await client.chat.completions.create({
  model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models (format is always `{org}/{model-name}`)

Common picks — verify the live list at `https://docs.together.ai/models`:

- `meta-llama/Llama-3.3-70B-Instruct-Turbo`, `meta-llama/Llama-3.3-70B-Instruct-Turbo-Free`
- `meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo`
- `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo`
- `deepseek-ai/DeepSeek-R1`, `deepseek-ai/DeepSeek-V3`
- `Qwen/Qwen2.5-72B-Instruct-Turbo`, `Qwen/Qwen3-235B-A22B-Instruct-2507`
- `mistralai/Mixtral-8x22B-Instruct-v0.1`
- `databricks/dbrx-instruct`
- `allenai/OLMo-2-1124-7B-Instruct`
- Image: `black-forest-labs/FLUX.1 schnell`, `stabilityai/stable-diffusion-xl`
- Embeddings: `togethercomputer/m2-bert-80M-8k-retrieval`
- Code FIM: `Qwen/Qwen2.5-Coder-32B-Instruct`

`-Turbo` variants are Together's optimized inference engine — faster and
cheaper than the base variant. Use them when present.

## Gotchas

- **Model id shape is strict**: `{org}/{model-name}` exactly as listed. A bare
  `Llama-3.3-70B-Instruct-Turbo` (no `meta-llama/`) will 404.
- **`-Turbo` variants** route to Together's optimized inference engine
  (different backend, lower latency, sometimes lower price).
- **`-Free` variants** have hard daily rate limits; fine for prototyping.
- **Reasoning field**: reasoning models (DeepSeek-R1, Qwen3-thinking) emit
  `delta.reasoning_content` (same convention as the upstream provider).
- **Fine-tuning**: upload JSONL → `POST /v1/fine-tunes` → result is a
  `model-name` you can call back through the same chat endpoint.
- **Tool calling**: standard OpenAI `tools`/`tool_calls` shape works on
  Instruct variants.
- **JSON mode**: `response_format={"type": "json_object"}` works on most
  instruct models; the model must be prompted to produce JSON.
