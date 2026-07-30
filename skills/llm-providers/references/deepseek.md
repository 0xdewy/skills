# DeepSeek

Chinese lab with an OpenAI-compatible hosted API — drop-in for the `openai` SDK.
(verified 2026-07; both `deepseek-chat` and `deepseek-reasoner` snippets in
this card were run live and returned the expected content and
`reasoning_content` separation.)

## Get an API key

`https://platform.deepseek.com/api_keys` → set `DEEPSEEK_API_KEY`. Keys look
like `sk-...` (no `proj` suffix).

```bash
export DEEPSEEK_API_KEY="sk-..."
```

## Base URL & auth

- Base URL: `https://api.deepseek.com/v1` (the host root
  `https://api.deepseek.com` also works — the SDK appends `/chat/completions`).
- Auth: `Authorization: Bearer $DEEPSEEK_API_KEY`
- Endpoint: `POST /chat/completions` (OpenAI-shaped)

## SDKs

Use the `openai` SDK pointed at the DeepSeek base URL. There is no first-party
SDK you need.

| Lang | Package |
|---|---|
| Python | `pip install openai` |
| TypeScript / Node | `npm install openai` |

## Samples

### curl

```bash
curl https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.deepseek.com/v1",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + reasoning (Python)

```python
client = OpenAI(base_url="https://api.deepseek.com/v1", api_key=os.environ["DEEPSEEK_API_KEY"])
stream = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[{"role": "user", "content": "Prove that the sum of two evens is even."}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta
    # R1 emits chain-of-thought in a separate field
    if getattr(delta, "reasoning_content", None):
        print(f"[think] {delta.reasoning_content}", end="", flush=True)
    elif delta.content:
        print(delta.content, end="", flush=True)
```

### TypeScript

```typescript
import OpenAI from "openai";
const client = new OpenAI({
  baseURL: "https://api.deepseek.com/v1",
  apiKey: process.env.DEEPSEEK_API_KEY,
});
const resp = await client.chat.completions.create({
  model: "deepseek-chat",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

- `deepseek-chat` — aliases to DeepSeek's current general flagship (DeepSeek-V3
  at launch; verified 2026-07 it returns `deepseek-v4-flash` as the underlying
  id, so the alias rolls forward as DeepSeek ships new generations — pin a
  specific snapshot id if you need reproducible behavior)
- `deepseek-reasoner` — DeepSeek-R1 reasoning model. Outputs chain of thought
  in `message.reasoning_content`; the final answer is in `message.content`.
  `temperature`, `top_p`, and most other sampling params are ignored.

Model list at `https://api-docs.deepseek.com/quick_start/pricing` is
authoritative. The V3/R1 weights are also on HuggingFace
(`deepseek-ai/DeepSeek-V3`, `deepseek-ai/DeepSeek-R1`) for self-hosting via
Together/Groq/your own vLLM.

## Gotchas

- **OpenAI-compat, not OpenAI**: works with the openai SDK as long as you set
  `base_url`. Don't expect newer OpenAI features (`reasoning_effort`, Responses
  API) to exist.
- **R1 reasoning field**: `delta.reasoning_content` is DeepSeek-specific —
  OpenAI's SDK passes it through but won't document it. Use `getattr(...,
  None)` defensively in Python.
- **JSON mode**: pass `response_format={"type": "json_object"}` like OpenAI,
  and prompt the model to produce JSON.
- **FIM / completions**: `/beta/completions` supports Fill-in-the-Middle for
  code editing (`prefix`/`suffix` body fields).
- **Region**: the international endpoint at `api.deepseek.com` is the
  recommended one for non-China users; mainland-only accounts may use
  `api.deepseek.com` after registering with a +86 phone — keys and pricing are
  the same.
- **Pricing is aggressive** vs. frontier US models; DeepSeek is a common pick
  when cost per token matters and a hosted OpenAI-compat endpoint is wanted.
