# Gemini MLLM Agent Config

Read this when changing the Python demo's voice model, greeting, prompt, VAD, or session options.

`server/src/agent.py` reads only `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, and
`GOOGLE_API_KEY` from `server/.env.local`. It constructs `AsyncAgora` and an
`AgoraAgent` with one `GeminiLive` provider. The selected public 3.8 model ID
is sent directly to the gateway. Extended Thinking defaults to thinking_level=medium.
The provider owns the system prompt, greeting, voice (`Puck`),
transcripts, and server VAD. There is no separate STT, LLM, or TTS stage.

Change `DEMO_GREETING` or `ADA_PROMPT` directly in that file.
The model switch includes medium thinking for
`models/gemini-3.8-live-extended-thinking` and omits it for
`models/gemini-3.8-live`. The SDK uses the Gemini preview gateway and
`agora-feature: gemini-live` automatically.

RTM, error messages, and metrics are enabled; tools are disabled. Session
options bind the agent UID and requester UID to one RTC channel, with a
30-second idle timeout and one-hour expiry. The service stores active sessions
for stop calls and has a preview-aware fallback when needed.

Verify with `server/venv/bin/python3 -m pytest server/tests` from the demo root.
A live check should start an agent, confirm its session `get_info().status` is
`RUNNING`, and stop it in a `finally` block.
