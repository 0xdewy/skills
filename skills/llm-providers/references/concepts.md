# Concepts (shared across LLM providers)

Patterns that apply to every card. Read this once; the per-provider cards
assume you know it. (verified 2026-07)

## Env-var convention

Every card tells you the canonical env-var name for that provider's key. The
universally accepted pattern is:

```bash
# one per provider; never share a var across vendors
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="AIza..."
export DEEPSEEK_API_KEY="sk-..."
export ZHIPU_API_KEY="..."            # Zhipu GLM
export MINIMAX_API_KEY="..."          # MiniMax international
export MISTRAL_API_KEY="...", COHERE_API_KEY="...", XAI_API_KEY="..."
export DASHSCOPE_API_KEY="..."        # Alibaba Qwen
export MOONSHOT_API_KEY="..."
export OPENROUTER_API_KEY="sk-or-..."
export TOGETHER_API_KEY="...", GROQ_API_KEY="gsk_..."
```

In code, read with a hard failure if absent — never fall back to an empty
string and never prompt the user to paste a key into the chat. Examples:

```python
import os
api_key = os.environ["OPENAI_API_KEY"]            # raises if missing
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Set OPENAI_API_KEY in the environment.")
```

```typescript
const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) throw new Error("Set OPENAI_API_KEY in the environment.");
```

Most official SDKs pick the env var up automatically when you instantiate a
client with no args (`OpenAI()`, `Anthropic()`, `Mistral()`, `OpenRouter()`).
Prefer that over passing the key explicitly.

## OpenAI-compatible endpoints

Most providers now expose an OpenAI-shaped Chat Completions surface. The
contract:

- Method: `POST {base_url}/chat/completions`
- Auth: `Authorization: Bearer <api_key>`
- Body: `{ "model": "<provider-model>", "messages": [...], "stream": true|false }`
- Response: OpenAI-shaped `choices[*].message.content`.

So the **same `openai` SDK** works against any of them — just point
`base_url` at the compat URL and use the provider's model string.

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://api.deepseek.com/v1",   # the compat URL from the card
    api_key=os.environ["DEEPSEEK_API_KEY"],
)
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "ping"}],
)
```

### Compat base URLs (verified 2026-07)

| Provider | OpenAI-compat `base_url` | Model string example |
|---|---|---|
| OpenAI (native) | `https://api.openai.com/v1` | `gpt-4.1` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Zhipu (GLM) | `https://open.bigmodel.cn/api/paas/v4` | `glm-4.6` |
| MiniMax (intl.) | `https://api.minimaxi.chat/v1` | `MiniMax-M2` |
| Xiaomi MiMo | `https://<your-host>/v1` (OSS weights) | `XiaomiMiMo-7B-RL` |
| Mistral | `https://api.mistral.ai/v1` | `mistral-large-latest` |
| xAI | `https://api.x.ai/v1` | `grok-4` |
| Alibaba Qwen (DashScope) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Moonshot (Kimi) | `https://api.moonshot.ai/v1` | `moonshot-v1-32k` |
| Together | `https://api.together.xyz/v1` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | `anthropic/claude-3.5-sonnet` |
| Cohere | `https://api.cohere.ai/compatibility/v1` | `command-r-08-2024` |

Anthropic and Google Gemini do **not** ship a first-party OpenAI-compat
endpoint (Anthropic offers one via the OpenAI SDK as a compatibility layer;
see `anthropic.md`). When a card says "not OpenAI-compatible natively", use
the native SDK.

When in doubt: prefer the compat endpoint for chat-only use cases (cheapest to
swap providers), and the native SDK when you need vendor-specific features
(prompt caching, multimodal, tool-calling details, embeddings, rerank).

## Streaming

Two equally valid patterns.

### SDK streaming (recommended)

```python
stream = client.chat.completions.create(model=..., messages=..., stream=True)
for chunk in stream:
    delta = chunk.choices[0].delta.content or ""
    print(delta, end="", flush=True)
```

```typescript
const stream = await client.chat.completions.create({ model, messages, stream: true });
for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
```

### SSE over raw HTTP

`Accept: text/event-stream`, then parse `data: {json}\n\n` lines. The terminal
sentinel is `data: [DONE]`. Only do this if you can't use an SDK.

Reasoning models (DeepSeek-R1, GLM-4.6 reasoning, Anthropic extended thinking,
OpenAI `o1`/`o3`, MiMo-RL, Qwen3-thinking) emit a separate field for chain of
thought: `delta.reasoning_content` (DeepSeek/GLM/MiniMax) or
`delta.thinking` (Anthropic). Don't conflate reasoning tokens with the answer.

## Tool calling (function calling)

OpenAI-compat providers all accept the `tools` array with JSON-Schema
`parameters`. Use it instead of regex-parsing the message when available:

```python
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
resp = client.chat.completions.create(model=..., messages=..., tools=tools)
call = resp.choices[0].message.tool_calls[0]
args = json.loads(call.function.arguments)
```

Anthropic uses `tools=[{name, description, input_schema}]` and returns
`stop_reason="tool_use"`; see `anthropic.md`. Gemini uses `functionDeclarations`
under `tools`. Native-shape differences are exactly when the vendor SDK beats
the compat endpoint.

## Retries, timeouts, rate limits

Every provider rate-limits and every request can fail. Make this baseline
mandatory in production:

- Set a per-request timeout (60s chat, 600s with long streaming/reasoning).
- Retry on 408/429/5xx with exponential backoff + jitter; do **not** retry 4xx
  (except 429). Cap at 3–5 attempts.
- Honor `Retry-After` on 429 when present.
- Bound concurrency well below the documented RPM/TPM.

```python
from openai import OpenAI
client = OpenAI(max_retries=4, timeout=60.0)   # SDK does backoff for you
```

The `openai`, `anthropic`, `mistral`, and `google-genai` SDKs all have
`max_retries`/`timeout` built in. For raw HTTP, wrap with
`tenacity` (Python) or a hand-rolled loop.

## Picking a provider

| If the user wants… | Reach for |
|---|---|
| Best general-purpose frontier model | OpenAI `gpt-4.1`/`gpt-5`, Anthropic `claude-opus-4`/`claude-sonnet-4`, Gemini `gemini-2.5-pro`/`gemini-3-pro` |
| Strong reasoning / math / code | Anthropic Claude (extended thinking), DeepSeek-R1, OpenAI `o3`/`o4`, GLM-4.6 reasoning, Qwen3-thinking |
| Cheap, very fast | Groq-hosted Llama 3.3 70B, OpenAI `gpt-4o-mini`, Gemini Flash, MiniMax-M2, DeepSeek-chat |
| Long context (>1M tokens) | Gemini (1M–2M), MiniMax-Text-01 (1M+), Claude (200k–1M), Moonshot `moonshot-v1-128k`/Kimi |
| Code generation | Codestral, DeepSeek-Coder-V3, Qwen-Coder, Grok Code, GLM-4.6 |
| Open models with full weight control | Together, OpenRouter, Groq (hosted), or self-host (Llama, Qwen, DeepSeek, MiMo weights on HuggingFace) |
| One SDK across many providers | OpenRouter, or the `openai` SDK pointed at each compat URL |

Cards below have the exact model strings and the per-provider quirks.

## Key safety checklist

- Read keys only from env or a secret manager. Never echo or log them.
- Don't hardcode a model string you didn't pull from the card or the provider's
  model page in the same session.
- For multimodal inputs (images, audio), the upload shape differs per provider
  — read the card's "Multimodal" section before guessing.
- Region restrictions: some Chinese providers (Zhipu, MiniMax CN, Qwen
  DashScope, Moonshot, Xiaomi) have separate international vs. mainland stacks
  with different base URLs and key registries. Cards call this out.
