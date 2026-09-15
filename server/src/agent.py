"""
Agent

High-level API for managing Agora Conversational AI Agents.
"""
import logging
import os
import time
from typing import Any, Dict, Optional

from agora_agent import Area, AsyncAgora
from agora_agent.agentkit import Agent as AgoraAgent
from agora_agent.agentkit import GeminiLive
from agora_agent.agentkit.preview import GeminiLiveModels, PreviewFeatures, create_preview_session_clients
from agora_agent.agentkit.token import generate_convo_ai_token
from agora_agent.core.api_error import ApiError

logger = logging.getLogger("uvicorn.error")

ADA_PROMPT = """You are Ada, an agentic developer advocate from Agora. You help developers understand and build with Agora's Conversational AI platform.

Agora is a real-time communications company. The product you represent is the Agora Conversational AI Engine.

If you do not know a specific fact about Agora, say so plainly and suggest checking docs.agora.io. Keep most replies to one or two sentences unless the user explicitly asks for more detail.
"""
DEMO_GREETING = "Hi there! I'm Ada, your virtual assistant from Agora. How can I help?"
DEMO_MODELS = {GeminiLiveModels.LIVE_38, GeminiLiveModels.LIVE_38_EXTENDED_THINKING}
THINKING_MODEL = "models/gemini-3.8-live-extended-thinking"
THINKING_LEVELS = {"low", "medium", "high"}


class Agent:
    """
    High-level wrapper for Agora Conversational AI Agent operations.
    
    Uses AgentSession for full lifecycle management (start/stop),
    which handles Token007 authentication automatically.
    """
    
    def __init__(self):
        self.app_id = os.getenv("AGORA_APP_ID")
        self.app_certificate = os.getenv("AGORA_APP_CERTIFICATE")
        self.greeting = DEMO_GREETING

        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required for the Gemini preview providers")

        if not self.app_id or not self.app_certificate:
            raise ValueError("AGORA_APP_ID and AGORA_APP_CERTIFICATE are required")

        # The session detects the Gemini MLLM and pins its preview route and gate.
        self.client = AsyncAgora(
            area=Area.US,
            app_id=self.app_id,
            app_certificate=self.app_certificate,
        )

        # Track active sessions by agent_id
        self._sessions: Dict[str, Any] = {}

    async def start(
        self,
        channel_name: str,
        agent_uid: int,
        user_uid: int,
        output_audio_codec: Optional[str] = None,
        model: str = "models/gemini-3.8-live",
        thinking_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start agent with the same default vendor chain as the Next.js quickstart."""
        if not channel_name or not str(channel_name).strip():
            raise ValueError("channel_name is required and cannot be empty")
        if agent_uid <= 0:
            raise ValueError("agent_uid is required and cannot be empty")
        if user_uid <= 0:
            raise ValueError("user_uid is required and cannot be empty")

        # Extended Thinking adds a reasoning budget.
        # In MLLM mode agent-level `instructions` is not sent, so the system
        # prompt goes on the vendor, where it serialises to mllm.params.instructions.
        if model not in DEMO_MODELS:
            raise ValueError("Invalid model")
        if thinking_level is not None and (model != THINKING_MODEL or thinking_level not in THINKING_LEVELS):
            raise ValueError("Invalid thinking level for model")
        thinking_level = (thinking_level or "medium") if model == THINKING_MODEL else None
        mllm = GeminiLive(
            api_key=self.google_api_key,
            model=model,
            instructions=ADA_PROMPT,
            thinking_level=thinking_level,
            voice="Puck",
            language_codes=["en-US"],
            transcribe_agent=True,
            transcribe_user=True,
            greeting_message=self.greeting,
            failure_message="Please wait a moment.",
            turn_detection={"mode": "server_vad"},
        )

        parameters = {
            "audio_scenario": "chorus",  # web client → ultra-low-latency chorus profile
            "data_channel": "rtm",
            "enable_error_message": True,
            "enable_metrics": True,
        }
        if isinstance(output_audio_codec, str) and output_audio_codec.strip():
            parameters["output_audio_codec"] = output_audio_codec.strip()

        agora_agent = AgoraAgent(
            client=self.client,
            greeting=self.greeting,
            advanced_features={"enable_rtm": True, "enable_tools": False},
            parameters=parameters,
        )
        
        agora_agent = agora_agent.with_mllm(mllm)

        session = agora_agent.create_async_session(
            channel=channel_name,
            agent_uid=str(agent_uid),
            remote_uids=[str(user_uid)],
            enable_string_uid=False,
            idle_timeout=30,
            expires_in=3600,
        )

        logger.info(
            "Starting Agora agent channel=%s agent_uid=%s user_uid=%s",
            channel_name,
            agent_uid,
            user_uid,
        )

        try:
            agent_id = await session.start()
        except Exception:
            logger.exception(
                "Failed to start Agora agent channel=%s agent_uid=%s user_uid=%s",
                channel_name,
                agent_uid,
                user_uid,
            )
            raise

        # Save session for later stop
        self._sessions[agent_id] = session

        logger.info(
            "Started Agora agent agent_id=%s channel=%s agent_uid=%s user_uid=%s",
            agent_id,
            channel_name,
            agent_uid,
            user_uid,
        )
        
        return {
            "agent_id": agent_id,
            "channel_name": channel_name,
            "status": "started",
        }

    async def stop(self, agent_id: str) -> None:
        """Stop a running agent. Falls back to the stateless client path."""
        if not agent_id or not str(agent_id).strip():
            raise ValueError("agent_id is required and cannot be empty")

        session = self._sessions.pop(agent_id, None)
        if session:
            try:
                await session.stop()
                logger.info("Stopped Agora agent from active session agent_id=%s", agent_id)
                return
            except Exception:
                # Fall back to the stateless SDK path if the in-memory session is stale.
                logger.warning(
                    "Failed to stop Agora agent from active session; falling back to client.stop_agent agent_id=%s",
                    agent_id,
                    exc_info=True,
                )

        # A stateless stop still needs Gemini's preview host and feature gate.
        preview_agents, _ = create_preview_session_clients(
            self.client, [PreviewFeatures.GEMINI_LIVE]
        )
        token = generate_convo_ai_token(
            app_id=self.app_id,
            app_certificate=self.app_certificate,
            channel_name="stop",
            uid=0,
        )
        try:
            await preview_agents.stop(
                self.app_id,
                agent_id,
                request_options={"additional_headers": {"Authorization": f"agora token={token}"}},
            )
        except ApiError as exc:
            if exc.status_code != 404:
                raise
