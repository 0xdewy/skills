# Google Gemini

Google's Gemini API. Two surfaces — **AI Studio / `generativelanguage`** (key
auth, easiest) and **Vertex AI** (Google Cloud IAM, enterprise). This card uses
AI Studio. (verified 2026-07)

## Get an API key

`https://aistudio.google.com/app/apikey` → set `GEMINI_API_KEY` (or
`GOOGLE_API_KEY`) in the environment. Keys look like `AIza...`.

```bash
export GEMINI_API_KEY="AIza..."
```

## Base URL & auth

- Base URL (AI Studio): `https://generativelanguage.googleapis.com/v1beta`
- Auth: either query param `?key=$GEMINI_API_KEY` or header
  `x-goog-api-key: $GEMINI_API_KEY`.
- Native endpoint per model:
  `POST /v1beta/models/{model}:generateContent`
- Streaming variant: `:streamGenerateContent` (returns SSE).

## SDKs

| Lang | Package | Import |
|---|---|---|
| Python | `pip install google-genai` | `from google import genai` |
| TypeScript / Node | `npm install @google/genai` | `import { GoogleGenAI } from "@google/genai"` |

The new `google-genai` SDK replaces the older `google-generativeai`; both AI
Studio and Vertex are reachable from the same constructor (`genai.Client(
vertexai=True, project=..., location=...)` for Vertex). Prefer `google-genai`
for new code.

## Samples

### curl

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Say hello in one short sentence."}]}]
  }'
```

### Python (native)

```python
import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello in one short sentence.",
)
print(resp.text)
```

### Streaming + tool (Python)

```python
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

get_weather = types.FunctionDeclaration(
    name="get_weather",
    description="Get current weather for a city.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"city": types.Schema(type="STRING")},
        required=["city"],
    ),
)
tools = [types.Tool(function_declarations=[get_weather])]

for chunk in client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents="What's the weather in Kyoto?",
    tools=tools,
):
    print(chunk.text or "", end="", flush=True)
```

For TypeScript, use `const ai = new GoogleGenAI({apiKey: process.env.GEMINI_API_KEY});`
and `await ai.models.generateContent(...)` / `generateContentStream(...)`.

## Current models (verify on ai.google.dev before shipping)

- `gemini-3-pro`, `gemini-3-flash` — latest flagship family (verify exact ids
  and dated snapshots against the model page)
- `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` — widely
  available, strong defaults
- `gemini-2.0-flash`, `gemini-2.0-flash-thinking-exp` — older but still in use
- Imagegen / Veo / TTS / STT are separate model ids
  (`gemini-2.5-flash-image`, `veo-3.0`, etc.).

The model list at `https://ai.google.dev/gemini-api/docs/models` is
authoritative.

## OpenAI compatibility

Google ships an OpenAI-compat endpoint:

- Base URL: `https://generativelanguage.googleapis.com/v1beta/openai/`
- Auth: `Authorization: Bearer $GEMINI_API_KEY`

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    api_key=os.environ["GEMINI_API_KEY"],
)
resp = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[{"role": "user", "content": "hi"}],
)
```

Use the compat endpoint for chat-only ports; use the native SDK for grounded
search, code execution, function calling nuances, and image/video IO.

## Gotchas

- **Request shape differs**: native uses `contents: [{parts: [{text}]}]`, not
  OpenAI's `messages: [{role, content}]`. Tool results come back in
  `candidates[0].content.parts[n].functionCall`.
- **Multimodal**: pass images inline as
  `{"inline_data": {"mime_type": "image/jpeg", "data": "<base64>"}}` or by
  `file_data` with a File API URI. PDFs, audio, and video are first-class.
- **Safety settings**: `safetySettings` lets you raise the threshold per
  category (e.g. `block_only_high`). The default filter is stricter than most
  providers — a request can return `candidates=[]` with a `promptFeedback`
  block instead of an error.
- **Long context**: Gemini models accept up to 1M+ tokens; large inputs should
  use the File API (`client.files.upload`) to avoid sending bytes per request.
- **Vertex AI**: same model ids, but auth is Google Cloud IAM
  (`gcloud auth application-default login`) and the base URL is regional
  (`https://{region}-aiplatform.googleapis.com/v1/projects/...`).
- **Grounding**: pass `tools=[{"google_search": {}}]` to let Gemini cite
  live web results.
