# Groq

GroqCloud hosts open models on Groq LPUs — OpenAI-compatible API, very low
latency. (verified 2026-07)

## Get an API key

`https://console.groq.com/keys` → set `GROQ_API_KEY`. Keys look like
`gsk_...`.

```bash
export GROQ_API_KEY="gsk_..."
```

## Base URL & auth

- Base URL: `https://api.groq.com/openai/v1`
- Auth: `Authorization: Bearer $GROQ_API_KEY`
- Endpoint: `POST /chat/completions` (OpenAI-shaped)
- Other surfaces: `POST /embeddings` (limited model set),
  `POST /openai/v1/audio/transcriptions` (Whisper-large-v3),
  `POST /openai/v1/audio/translations`,
  `POST /openai/v1/audio/speech` (PlayAI TTS).

## SDKs

| Lang | Package | Import |
|---|---|---|
| Python | `pip install groq` | `from groq import Groq` |
| TypeScript / Node | `npm install groq-sdk` | `import Groq from "groq-sdk"` |
| Any | `pip install openai` | works at the compat URL |

## Samples

### curl

```bash
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}]
  }'
```

### Python (native SDK)

```python
import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])
resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Python (OpenAI SDK at the compat URL)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
)
resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(resp.choices[0].message.content)
```

### Streaming + reasoning (DeepSeek-R1 distill)

```python
stream = client.chat.completions.create(
    model="deepseek-r1-distill-llama-70b",
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

### Tool call (Python)

```python
resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
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
    tool_choice="auto",
)
call = resp.choices[0].message.tool_calls[0]
print(call.function.name, call.function.arguments)
```

### TypeScript

```typescript
import Groq from "groq-sdk";
const client = new Groq({ apiKey: process.env.GROQ_API_KEY });
const resp = await client.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});
console.log(resp.choices[0].message.content);
```

## Current models

Verify the live list at `https://console.groq.com/docs/models`:

- `llama-3.3-70b-versatile`, `llama-3.3-70b-specdec`
- `llama-3.1-8b-instant`
- `llama3-70b-8192`, `llama3-8b-8192` (older generation)
- `deepseek-r1-distill-llama-70b`, `deepseek-r1-distill-qwen-32b`
- `moonshotai/Kimi-K2-Instruct`
- `qwen-2.5-32b`, `qwen-2.5-coder-32b`
- `gemma2-9b-it`
- `playai-tts`, `playai-tts-arabic` — text-to-speech
- `whisper-large-v3`, `whisper-large-v3-turbo` — speech-to-text

## Gotchas

- **Speed**: Groq's selling point is first-token latency. Batched/embeddings
  use cases are usually better served elsewhere.
- **Reasoning field**: distills of DeepSeek-R1 emit
  `delta.reasoning_content` (same convention as upstream).
- **Rate limits**: dev tier has low RPM (e.g. 30). Production tier requires
  upgrading in the console; check the dashboard on 429s.
- **Context windows**: smaller than upstream providers — most models cap at
  32k or 128k; check the model page before sending long inputs.
- **JSON mode**: `response_format={"type": "json_object"}` works; the model
  must be prompted to produce JSON.
- **Audio**: transcription / TTS endpoints are OpenAI-shaped — same code as
  `openai.audio.transcriptions.create` works against Groq's compat URL.
