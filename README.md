# agora-gemini-mllm — Python demo

This demo pairs a Next.js voice client with a FastAPI backend and the published Agora Python Agent SDK. One `GeminiLive` provider handles audio input and output end to end; there is no separate STT, LLM, or TTS stage.

The browser chooses `models/gemini-3.8-live` or `models/gemini-3.8-live-extended-thinking`. Extended Thinking exposes a low/medium/high slider; the regular model sends no thinking level. `POST /api/startAgent` carries the public model ID and optional `thinkingLevel`; FastAPI validates the selection. The SDK routes Gemini sessions to the preview gateway with `agora-feature: gemini-live` and sends the Google credential as `mllm.api_key`.

## Requirements

- Python 3.10+, Bun, and Node.js 22+.
- Agora App ID, App Certificate, and Google API key.

## Run locally

From this demo folder:

```bash
bun run setup
# Fill AGORA_APP_ID, AGORA_APP_CERTIFICATE, and GOOGLE_API_KEY in server/.env.local.
bun run dev:parallel
```

FastAPI listens on `http://localhost:8110`. Next.js chooses an available frontend port; open the Local URL it prints. The browser calls Next `/api/*` paths, which rewrite to FastAPI. The local credential file needs only the three secrets above. Prompt, greeting, model, voice, and session settings live in `server/src/agent.py`.

## Verify

```bash
cd server && venv/bin/python3 -m pytest tests
cd ..
bun run verify:web
```

The API and proxy checks run without cloud credentials. For a real connection, start the demo with valid credentials, confirm the agent reaches `RUNNING`, and stop it.

## Deploy

Deploy `web/` and `server/` separately. Set `AGENT_BACKEND_URL` in the Next.js deployment to the public FastAPI backend URL. Keep `AGORA_APP_CERTIFICATE` and `GOOGLE_API_KEY` on the server. The Gemini models in this demo still require the preview gateway.

See [ARCHITECTURE.md](./ARCHITECTURE.md), [AGENTS.md](./AGENTS.md), and the [recipe contract](./docs/ai/RECIPE.md) for the request flow and extension points. Licensed under [MIT](./LICENSE).
