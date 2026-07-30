# Anthropic (Claude)

Native Claude API. Anthropic also exposes an OpenAI-compat shim — see the
"OpenAI compatibility" section below. (verified 2026-07)

## Get an API key

`https://console.anthropic.com/` → set `ANTHROPIC_API_KEY` in the environment.
Keys look like `sk-ant-...`.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Base URL & auth

- Base URL: `https://api.anthropic.com/v1`
- Required headers for every native request:
  - `x-api-key: $ANTHROPIC_API_KEY`
  - `anthropic-version: 2023-06-01`
  - `Content-Type: application/json`
- Endpoint: `POST /v1/messages`

## SDKs

| Lang | Package | Import |
|---|---|---|
| Python | `pip install anthropic` | `from anthropic import Anthropic` |
| TypeScript / Node | `npm install @anthropic-ai/sdk` | `import Anthropic from "@anthropic-ai/sdk"` |

Both auto-pick `ANTHROPIC_API_KEY` from env. Also available on AWS Bedrock
(`AnthropicBedrock`) and Google Vertex AI (`AnthropicVertex`) — different
constructor, same SDK.

## Samples

### curl

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 256,
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python

```python
import os
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY
msg = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=256,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(msg.content[0].text)
```

### Streaming + tool use (Python)

```python
import json
from anthropic import Anthropic

client = Anthropic()
tools = [{
    "name": "get_weather",
    "description": "Get current weather for a city.",
    "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
}]

with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Kyoto?"}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

When the model stops with `stop_reason="tool_use"`, read
`msg.content` for a `tool_use` block, run the tool, then continue the
conversation with a `tool_result` user message.

### TypeScript

```typescript
import Anthropic from "@anthropic-ai/sdk";
const client = new Anthropic(); // reads ANTHROPIC_API_KEY

const msg = await client.messages.create({
  model: "claude-sonnet-4-5-20250929",
  max_tokens: 256,
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(msg.content[0].text);
```

## Current models (verify on docs.anthropic.com before shipping)

- `claude-opus-4-0-20250514`, `claude-opus-4-5-...` — flagship, hardest tasks
- `claude-sonnet-4-20250514`, `claude-sonnet-4-5-20250929` — balanced workhorse
- `claude-haiku-4-5-...`, `claude-3-5-haiku-20241022` — cheap, fast
- Extended-thinking variants: pass `thinking={"type": "enabled",
  "budget_tokens": N}` to surface reasoning before the answer.

The model list at `https://docs.anthropic.com/en/docs/about-claude/models` is
authoritative; Anthropic also publishes dated snapshots (e.g.
`-20250929`) which pin behavior.

## OpenAI compatibility

Anthropic ships a compatibility shim for the `openai` SDK:

- Base URL: `https://api.anthropic.com/v1/openai/`
- Auth: `Authorization: Bearer $ANTHROPIC_API_KEY` (the shim also requires
  `anthropic-version` — the SDK adds it).

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://api.anthropic.com/v1/openai",
    api_key=os.environ["ANTHROPIC_API_KEY"],
)
resp = client.chat.completions.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "hi"}],
)
```

Use it for quick ports. For prompt caching, extended thinking, native tool
use, citations, or batched / async jobs, use the native SDK.

## Gotchas

- **No `system` field in `messages`**: pass system prompts as a top-level
  `system` parameter, not a message with `role: "system"`.
- **`max_tokens` is required** for every request (other providers default it;
  Anthropic does not).
- **Prompt caching**: add `cache_control: {type: "ephemeral"}` to a content
  block to memoize long system prompts / docs — cuts latency and cost on
  repeated context. Billed at cache-write/cache-read rates.
- **Image inputs**: pass as `{"type": "image", "source": {"type": "base64",
  "media_type": "image/jpeg", "data": "..."}}` inside a `content` array.
- **Token counting**: `client.messages.count_tokens(...)` to preview usage
  without making a completion.
- **Bedrock / Vertex**: same `messages.create` shape but constructor and auth
  differ (`AnthropicBedrock(aws_region=...)`, `AnthropicVertex()`); model ids
  are prefixed (`anthropic.claude-sonnet-4-5-20250929-v1:0` on Bedrock).
