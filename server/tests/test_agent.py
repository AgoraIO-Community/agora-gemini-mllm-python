"""Gemini preview agent wiring and lifecycle tests (no cloud requests)."""
import asyncio
import sys

import pytest


def _fresh_agent_module():
    sys.modules.pop("agent", None)
    import agent
    return agent


@pytest.mark.parametrize("missing", ["AGORA_APP_ID", "AGORA_APP_CERTIFICATE", "GOOGLE_API_KEY"])
def test_agent_requires_env(fake_env, monkeypatch, missing):
    monkeypatch.delenv(missing, raising=False)
    agent = _fresh_agent_module()
    with pytest.raises(ValueError):
        agent.Agent()


def test_agent_constructs_with_full_env(fake_env):
    agent = _fresh_agent_module()
    instance = agent.Agent()
    assert instance.app_id == fake_env["AGORA_APP_ID"]
    assert instance.client is not None


def test_start_wires_gemini_preview_and_returns_shape(fake_env, monkeypatch):
    agent = _fresh_agent_module()
    captured = {}

    class FakeSession:
        async def start(self):
            return "test-agent-id"

        async def stop(self):
            captured["stopped"] = True

    def fake_create_async_session(self, **kwargs):
        captured["mllm"] = self._mllm
        captured["channel"] = kwargs.get("channel")
        captured["remote_uids"] = kwargs.get("remote_uids")
        return FakeSession()

    from agora_agent.agentkit import Agent as AgoraAgent
    monkeypatch.setattr(AgoraAgent, "create_async_session", fake_create_async_session)

    instance = agent.Agent()
    result = asyncio.run(instance.start(channel_name="ch", agent_uid=111, user_uid=222, model="models/gemini-3.8-live-extended-thinking", thinking_level="medium"))
    assert result == {
        "agent_id": "test-agent-id",
        "channel_name": "ch",
        "status": "started",
    }
    mllm = captured["mllm"]
    assert mllm["vendor"] == "gemini"
    assert mllm["params"]["model"] == "models/gemini-3.8-live-extended-thinking"
    assert mllm["params"]["language_codes"] == ["en-US"]
    assert mllm["api_key"] == fake_env["GOOGLE_API_KEY"]
    assert "api_key" not in mllm["params"]
    assert mllm["greeting"] == instance.greeting
    assert "greeting_message" not in mllm
    assert "language" not in mllm["params"]
    assert mllm["params"]["thinking_level"] == "medium"
    assert captured["channel"] == "ch"
    assert captured["remote_uids"] == ["222"]


def test_start_validates_arguments(fake_env):
    agent = _fresh_agent_module()
    instance = agent.Agent()
    with pytest.raises(ValueError):
        asyncio.run(instance.start(channel_name="", agent_uid=1, user_uid=2))
    with pytest.raises(ValueError):
        asyncio.run(instance.start(channel_name="c", agent_uid=0, user_uid=2))
    with pytest.raises(ValueError, match="Invalid model"):
        asyncio.run(instance.start(channel_name="c", agent_uid=1, user_uid=2, model="unknown"))
    with pytest.raises(ValueError, match="Invalid thinking level"):
        asyncio.run(instance.start(channel_name="c", agent_uid=1, user_uid=2, model="models/gemini-3.8-live", thinking_level="high"))
    with pytest.raises(ValueError, match="Invalid thinking level"):
        asyncio.run(instance.start(channel_name="c", agent_uid=1, user_uid=2, model="models/gemini-3.8-live-extended-thinking", thinking_level="extreme"))


@pytest.mark.parametrize("model,level,expected_model,expected_level", [
    ("models/gemini-3.8-live", None, "models/gemini-3.8-live", None),
    ("models/gemini-3.8-live-extended-thinking", "low", "models/gemini-3.8-live-extended-thinking", "low"),
    ("models/gemini-3.8-live-extended-thinking", "medium", "models/gemini-3.8-live-extended-thinking", "medium"),
    ("models/gemini-3.8-live-extended-thinking", "high", "models/gemini-3.8-live-extended-thinking", "high"),
])
def test_model_selection_controls_vendor_payload(fake_env, monkeypatch, model, level, expected_model, expected_level):
    agent = _fresh_agent_module()
    captured = {}

    class FakeSession:
        async def start(self):
            return "agent-selected"

    from agora_agent.agentkit import Agent as AgoraAgent
    def fake_session(self, **kwargs):
        captured["mllm"] = self._mllm
        return FakeSession()
    monkeypatch.setattr(AgoraAgent, "create_async_session", fake_session)
    asyncio.run(agent.Agent().start("ch", 111, 222, model=model, thinking_level=level))
    params = captured["mllm"]["params"]
    assert params["model"] == expected_model
    if expected_level is None:
        assert "thinking_level" not in params
    else:
        assert params["thinking_level"] == expected_level


def test_stop_uses_active_session_then_preview_fallback(fake_env, monkeypatch):
    agent = _fresh_agent_module()

    class FakeSession:
        stopped = False

        async def start(self):
            return "agent-xyz"

        async def stop(self):
            self.stopped = True

    session = FakeSession()
    from agora_agent.agentkit import Agent as AgoraAgent
    monkeypatch.setattr(AgoraAgent, "create_async_session", lambda self, **k: session)
    instance = agent.Agent()
    fallback_calls = []

    class FakePreviewAgents:
        async def stop(self, app_id, agent_id, request_options):
            fallback_calls.append((app_id, agent_id, request_options))

    monkeypatch.setattr(agent, "create_preview_session_clients",
        lambda client, features: (FakePreviewAgents(), None))
    monkeypatch.setattr(agent, "generate_convo_ai_token", lambda **kwargs: "fake-token")

    asyncio.run(instance.start(channel_name="ch", agent_uid=111, user_uid=222))
    asyncio.run(instance.stop("agent-xyz"))
    assert session.stopped is True
    assert fallback_calls == []

    asyncio.run(instance.stop("unknown-id"))
    assert fallback_calls == [(
        fake_env["AGORA_APP_ID"],
        "unknown-id",
        {"additional_headers": {"Authorization": "agora token=fake-token"}},
    )]
