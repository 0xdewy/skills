# References index

Routing table only — load the one file that matches the task. For a targeted
lookup across all files, run `python scripts/search_refs.py "<terms>"`.

Per-provider cards each carry: where to get a key, canonical env var, REST
base URL, auth header, OpenAI-compatibility, official Python/TypeScript SDK
packages, working `curl`/Python/TS samples, current model names, and gotchas.
Model lineups drift — verify against the provider's docs if your task postdates
the card's "verified" date.

(last verified: 2026-07)

## Cross-cutting

| Load this file when… | File |
|---|---|
| Comparing providers, picking a model, or explaining OpenAI-compat, streaming, retries, tool calling, or the env-var convention | `concepts.md` |

## Providers (first-party / native APIs)

| Provider | Load | Card covers |
|---|---|---|
| OpenAI | `openai.md` | GPT, reasoning models, Responses + Chat Completions APIs |
| Anthropic (Claude) | `anthropic.md` | Claude, Messages API, prompt caching, Bedding/Vertex |
| Google Gemini | `google-gemini.md` | Gemini, generateContent, multimodal, AI Studio + Vertex |
| DeepSeek | `deepseek.md` | DeepSeek-V3, DeepSeek-R1, OpenAI-compat |
| Zhipu (GLM) | `zhipu-glm.md` | GLM-4, GLM-4.5, GLM-4.6, reasoning, OpenAI-compat |
| MiniMax | `minimax.md` | abab, MiniMax-Text-01, M1, OpenAI-compat (intl.) |
| Xiaomi (MiMo) | `xiaomi-mimo.md` | MiMo-7B, MiMo-VL, OpenAI-compat |
| Mistral | `mistral.md` | Mistral Large, Codestral, Magistral, OpenAI-compat |
| xAI (Grok) | `xai.md` | Grok, Grok reasoning, OpenAI-compat |
| Alibaba (Qwen) | `alibaba-qwen.md` | Qwen, Qwen3, DashScope + OpenAI-compat |
| Moonshot (Kimi) | `moonshot-kimi.md` | Kimi K1.5, Moonshot, OpenAI-compat |
| Cohere | `cohere.md` | Command R+, embeddings, rerank, v2 Chat |

## Aggregators (one API, many models)

| Provider | Load | Card covers |
|---|---|---|
| OpenRouter | `openrouter.md` | 100+ models via OpenAI-compat, routing + pricing |
| Together AI | `together.md` | hosted open models, OpenAI-compat |
| Groq | `groq.md` | LPU-hosted open models, OpenAI-compat, very fast |

## Common quick picks

- "I just want OpenAI-compat base URLs for all of them at once" —
  `concepts.md` → "OpenAI-compatible endpoints" has the table.
- "What env var do I set?" — `concepts.md` → "Env-var convention".
- "How do I stream / call tools / retry?" — `concepts.md`.
