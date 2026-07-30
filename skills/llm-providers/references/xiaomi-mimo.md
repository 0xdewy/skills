# Xiaomi MiMo

Xiaomi's MiMo is a family of **open-weight** models (MiMo-7B, MiMo-VL) — there
is no first-party hosted API. "Setting up a connection" means deploying the
weights behind an OpenAI-compatible inference server. (verified 2026-07)

## Where the weights live

- HuggingFace org: `https://huggingface.co/XiaomiMiMo`
- GitHub: `https://github.com/XiaomiMimo`
- Flagship repos:
  - `XiaomiMiMo/MiMo-7B-RL` — reasoning-tuned 7B, OpenAI-compat when served
  - `XiaomiMiMo/MiMo-7B-RL-8bit` — quantized
  - `XiaomiMiMo/MiMo-7B-SFT` — SFT base for custom fine-tunes
  - `XiaomiMiMo/MiMo-VL-7B-RL` — vision-language

There is **no key from Xiaomi**. Authentication is whatever your inference
server enforces.

## Base URL & auth

- Base URL: the address of your inference server (commonly
  `http://localhost:8000/v1` for vLLM, SGLang, TGI; or a hosted endpoint on
  Together / SiliconFlow / HuggingFace Inference Endpoints).
- Auth: usually `Authorization: Bearer $YOUR_SERVER_TOKEN` — vLLM's OpenAI
  server takes `--api-key`; set the same value client-side. Local dev usually
  disables auth.
- Endpoint: `POST /v1/chat/completions` (OpenAI-shaped) when served with vLLM
  or SGLang.

## SDKs

Any OpenAI-compatible client works once the server is up:

| Lang | Package |
|---|---|
| Python | `pip install openai` |
| TypeScript / Node | `npm install openai` |
| Server | `pip install vllm` or `pip install sglang[all]` |

## Deploy (vLLM)

```bash
pip install vllm
# Downloads ~15 GB from HuggingFace on first run
vllm serve XiaomiMiMo/MiMo-7B-RL \
  --served-model-name XiaomiMiMo-7B-RL \
  --api-key sk-local-dev \
  --host 0.0.0.0 --port 8000
```

This exposes `http://localhost:8000/v1/chat/completions` in OpenAI shape.

## Samples

### curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-local-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "XiaomiMiMo-7B-RL",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.environ.get("MIMO_API_KEY", "sk-local-dev"),
    model="XiaomiMiMo-7B-RL",
)
resp = client.chat.completions.create(
    model="XiaomiMiMo-7B-RL",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + reasoning

MiMo-7B-RL was trained with a `<|im_start|>think ... <|im_end|>` segment.
vLLM/SGLang surface this as a `reasoning_content` field on the delta when the
chat template parses it; otherwise it appears inline in `content` between the
tokens. Read both fields defensively:

```python
stream = client.chat.completions.create(
    model="XiaomiMiMo-7B-RL",
    messages=[{"role": "user", "content": "Prove sum of two evens is even."}],
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
  baseURL: "http://localhost:8000/v1",
  apiKey: process.env.MIMO_API_KEY ?? "sk-local-dev",
});
const resp = await client.chat.completions.create({
  model: "XiaomiMiMo-7B-RL",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

- `XiaomiMiMo/MiMo-7B-RL` — recommended default; reasoning-strong for its size
- `XiaomiMiMo/MiMo-7B-RL-8bit` — reduced memory footprint
- `XiaomiMiMo/MiMo-7B-SFT` — SFT only; no reasoning segment
- `XiaomiMiMo/MiMo-VL-7B-RL` — vision + text; serve with a multimodal image
  input (`{"type": "image_url", "image_url": {"url": "..."}}`)

The HuggingFace org page is authoritative for new releases.

## Gotchas

- **No hosted API**: every "key" in code is whatever your inference server
  sets. Don't invent an `XIAOMI_API_KEY`.
- **Chat template**: MiMo uses an OpenAI-style `messages` chat template with a
  dedicated `think` role. vLLM loads it automatically; if you call the
  `/generate` endpoint raw, you must render the template yourself or you will
  lose the reasoning segment.
- **Hardware**: 7B in bf16 needs ~14 GB VRAM; the 8-bit variant fits in ~8 GB.
  CPU-only inference via `llama.cpp` / `MLX` also works.
- **Hosted alternatives**: SiliconFlow, ModelScope, and Together periodically
  host MiMo — the OpenAI-compat code above works unchanged against those URLs;
  just swap `base_url` and `api_key`.
- **Self-host safety**: when exposing a vLLM server beyond localhost, always
  set `--api-key` and put it behind a reverse proxy with rate limits; an
  unprotected OpenAI-compat server is an open prompt-injection target.
