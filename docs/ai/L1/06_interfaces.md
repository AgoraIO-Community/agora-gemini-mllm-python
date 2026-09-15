# 06 Interfaces

> Boundary contracts: FastAPI routes, Next rewrites, environment variables, and managed agent payload.

## Python Backend Routes

`server/src/server.py` registers these on an `APIRouter`:

| Path           | Method | Request                                                                              | Success (200)                                                                                | Errors                                                          |
| -------------- | ------ | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `/get_config`  | GET    | Query: optional `channel`, optional `uid`                                            | `{ "code": 0, "msg": "success", "data": { app_id, token, uid, channel_name, agent_uid } }`   | `500` if `agent is None`; exceptions via `_to_http_error`        |
| `/startAgent`  | POST   | JSON `StartAgentRequest`: `channelName`, `rtcUid`, `userUid`, optional `model`, `thinkingLevel`, `parameters` | `{ "code": 0, "msg": "success", "data": { agent_id, channel_name, status } }` | `400` validation (`ValueError`); `500` runtime / generic |
| `/stopAgent`   | POST   | JSON `StopAgentRequest`: `agentId`                                                   | `{ "code": 0, "msg": "success" }`                                                            | Same shape                                                       |

CORS middleware: `allow_origins=["*"]`, `allow_credentials=True`.

`StartAgentRequest.parameters` is optional — the handler only reads `output_audio_codec` from it today.

`get_config` treats missing, zero, and negative UIDs as "generate a random user UID" and returns the generated value. This keeps the single RTC+RTM token usable for RTM, where `0` is not a valid login subject.

## Next.js Rewrites

`web/next.config.ts` registers these only when `AGENT_BACKEND_URL` is set:

| Source             | Destination                                  |
| ------------------ | -------------------------------------------- |
| `/api/get_config`  | `${AGENT_BACKEND_URL}/get_config`             |
| `/api/startAgent`  | `${AGENT_BACKEND_URL}/startAgent`             |
| `/api/stopAgent`   | `${AGENT_BACKEND_URL}/stopAgent`              |

`verify-api-contracts.ts` asserts that no `web/app/api/**/route.ts` files exist. Adding one would create a competing handler in front of the rewrite — don't.

## Environment Variables

| Scope                  | Variable                                  |
| ---------------------- | ----------------------------------------- |
| Python server (required) | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE` |
| Python server (required) | `GOOGLE_API_KEY` (pass `PORT` only at launch)                 |
| Next build             | `AGENT_BACKEND_URL`                       |
| Browser                | `DEFAULT_AGENT_UID` in browser code        |

`AGENT_BACKEND_URL` is a Next **server**-time env var (used inside `next.config.ts`), not a `NEXT_PUBLIC_*` value — do not prefix it.

## Token Shape

`get_config` returns:

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "app_id": "string",
    "token": "string",          // built by generate_convo_ai_token, token_expire=3600
    "uid": "string",            // serialized number
    "channel_name": "string",
    "agent_uid": "string"
  }
}
```

The same token grants RTC and RTM privileges.

## Gemini MLLM Agent Payload

`server/src/agent.py` uses the SDK builder with one `GeminiLive` provider.
`model` chooses `models/gemini-3.8-live` or
`models/gemini-3.8-live-extended-thinking`. Extended Thinking uses the selected
`thinkingLevel` (`low`, `medium`, or `high`; default `medium`); Gemini 3.8 Live
sends none. FastAPI sends public IDs directly to the preview gateway.
The provider owns the system prompt,
greeting, voice, transcripts, and server VAD. The session selects the Agora
preview route and feature header automatically, then starts in the requester's
RTC channel. No separate STT, LLM, or TTS vendor is configured.

## RTM Event Shapes (Client-Side)

`AgoraVoiceAI` emits the same toolkit events as the other quickstarts:

- `TRANSCRIPT_UPDATED` — `{ uid, text, status, timestamp }[]`
- `AGENT_STATE_CHANGED` — `AgentState`
- `AGENT_METRICS` — `{ type, name, value, timestamp }`
- `MESSAGE_ERROR` — `{ module, code, message, send_ts }`
- `MESSAGE_SAL_STATUS` — `{ status, timestamp }`
- `AGENT_ERROR` — SDK error info

`ConversationComponent.tsx` also attaches a raw RTM `message` listener as a fallback for the same `message.error` / `message.sal_status` payloads.

## Internal Types

| Type                          | Lives in                                       | Notes                                            |
| ----------------------------- | ---------------------------------------------- | ------------------------------------------------ |
| `StartAgentRequest`           | `server/src/server.py`                         | pydantic, camelCase fields                       |
| `StopAgentRequest`            | `server/src/server.py`                         | pydantic, `agentId`                              |
| `AgoraTokenData`              | `web/src/types/conversation.ts`                | Used by `LandingPage` + `ConversationComponent`  |
| `AgoraRenewalTokens`          | `web/src/types/conversation.ts`                | Renewal handler payload                          |
| `ConversationComponentProps`  | `web/src/types/conversation.ts`                | Includes RTM client + data                       |
| `GetConfigResponse`           | `web/src/services/api.ts`                      | Browser shape for `data` field                   |

## Related Deep Dives

- [Managed Agent Config](L2/managed_agent_config.md) — Detailed field reference.
- [Verification Scripts](L2/verification_scripts.md) — How the contracts above are enforced by local pre-ship checks.
