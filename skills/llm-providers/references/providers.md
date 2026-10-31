# Providers

Stable connection facts, verified 2026-07. No model IDs: fetch them from the
models page or `GET {compat base}/models` at task time.

| Provider | Env var | Native base URL + auth | OpenAI-compat base URL | SDK py / ts | Models page |
|---|---|---|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `https://api.openai.com/v1`, Bearer | same | `openai` / `openai` | https://platform.openai.com/docs/models |
| Anthropic | `ANTHROPIC_API_KEY` | `https://api.anthropic.com/v1`, `x-api-key` + `anthropic-version: 2023-06-01` | `https://api.anthropic.com/v1/openai/` (shim) | `anthropic` / `@anthropic-ai/sdk` | https://docs.anthropic.com/en/docs/about-claude/models |
| Google Gemini | `GEMINI_API_KEY` | `https://generativelanguage.googleapis.com/v1beta`, `x-goog-api-key` or `?key=` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `google-genai` / `@google/genai` | https://ai.google.dev/gemini-api/docs/models |
| DeepSeek | `DEEPSEEK_API_KEY` | compat only, Bearer | `https://api.deepseek.com/v1` | `openai` / `openai` | https://api-docs.deepseek.com/quick_start/pricing |
| Zhipu GLM | `ZHIPU_API_KEY` | compat, Bearer | `https://open.bigmodel.cn/api/paas/v4` (mainland), `https://api.z.ai/api/paas/v4` (intl) | `zhipuai` / `zhipuai` | https://docs.z.ai, https://open.bigmodel.cn/dev/api |
| MiniMax | `MINIMAX_API_KEY` | compat, Bearer | `https://api.minimaxi.chat/v1` (intl), `https://api.minimax.chat/v1` (mainland) | `openai` | https://platform.minimaxi.com/document/Models |
| Xiaomi MiMo | your server's token | none: open weights, self-host with vLLM/SGLang | your server, e.g. `http://localhost:8000/v1` | `openai` | https://huggingface.co/XiaomiMiMo |
| Mistral | `MISTRAL_API_KEY` | `https://api.mistral.ai/v1`, Bearer | same | `mistralai` / `@mistralai/mistralai` | https://docs.mistral.ai/getting-started/models/models_overview |
| xAI | `XAI_API_KEY` | compat, Bearer | `https://api.x.ai/v1` | `openai` (`xai-sdk` py) | https://docs.x.ai/docs/models |
| Alibaba Qwen | `DASHSCOPE_API_KEY` | `https://dashscope.aliyuncs.com/api/v1`, Bearer | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `dashscope` / `openai` | https://help.aliyun.com/zh/model-studio/getting-started/models |
| Moonshot Kimi | `MOONSHOT_API_KEY` | compat, Bearer | `https://api.moonshot.ai/v1` (intl), `https://api.moonshot.cn/v1` (mainland) | `openai` | https://platform.moonshot.ai/docs/intro |
| Cohere | `COHERE_API_KEY` | `https://api.cohere.com/v2`, Bearer | `https://api.cohere.ai/compatibility/v1` (chat only) | `cohere` / `cohere-ai` | https://docs.cohere.com/docs/models |
| OpenRouter | `OPENROUTER_API_KEY` | compat, Bearer | `https://openrouter.ai/api/v1` | `openai` | https://openrouter.ai/models |
| Together | `TOGETHER_API_KEY` | compat, Bearer | `https://api.together.xyz/v1` | `together` / `together-ai` | https://docs.together.ai/models |
| Groq | `GROQ_API_KEY` | compat, Bearer | `https://api.groq.com/openai/v1` | `groq` / `groq-sdk` | https://console.groq.com/docs/models |

## Gotchas

- **Anthropic**: native API needs `max_tokens` on every request and takes
  `system` as a top-level field, not a message. Tool calls use
  `input_schema` and `stop_reason="tool_use"`.
- **Gemini**: native body is `contents: [{parts: [{text}]}]`; tools are
  `functionDeclarations`. Vertex AI uses Google Cloud IAM and regional URLs.
- **OpenAI**: reasoning models reject `temperature`/`top_p`. Responses API
  (`/v1/responses`) is OpenAI-only; use Chat Completions for portability.
- **Zhipu, MiniMax, Moonshot**: mainland and international keys are not
  interchangeable. MiniMax intl keys work only on `api.minimaxi.chat`.
- **Qwen**: a key needs an Alibaba Cloud China account; international users
  can reach Qwen via OpenRouter or Together.
- **MiniMax**: the compat endpoint returns reasoning as `<think>…</think>`
  inside `content`; the native endpoint needs a `GroupId` query param.
- **Cohere**: the compat shim is chat only; embed, rerank, and classify need
  the native SDK.
- **OpenRouter**: optional `HTTP-Referer` and `X-Title` headers for
  attribution; routing options go in `extra_body`.
- **Together**: model IDs are `{org}/{model}` exactly as listed.
- **MiMo**: there is no Xiaomi key or hosted API. Never expose a vLLM server
  beyond localhost without `--api-key`.
