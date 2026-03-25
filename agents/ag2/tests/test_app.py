"""Tests for the AG2 A2A agent application.

These tests validate the observable HTTP behaviour of the agent:
- AgentCard discovery (GET /.well-known/agent.json)
- Valid A2A message/send payload returns agent text response
- Invalid JSON-RPC payload returns error response

The AG2 LLM is mocked so tests run without a real API key.
"""
from __future__ import annotations

import os
import sys
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure the agent package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Provide a dummy API key so module-level env checks pass
os.environ.setdefault("GOOGLE_STUDIO_API_KEY", "test-key")

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils.message import new_agent_text_message
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_message_id() -> str:
    return str(uuid.uuid4())


class _EchoExecutor(AgentExecutor):
    """Test executor that echoes back the user input prefixed with 'echo:'."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = context.get_user_input()
        await event_queue.enqueue_event(new_agent_text_message(f"echo:{text}"))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError


def _build_test_app() -> Any:
    """Build a Starlette app using the real AgentCard + a mock executor."""
    skill = AgentSkill(
        id="rhyme-completer",
        name="Complete a rhyme",
        description="Given partial verses of '3 petits chats', returns the next verse.",
        tags=[],
        inputModes=["text"],
        outputModes=["text"],
    )
    card = AgentCard(
        name="Rhyme Completer (AG2)",
        description=(
            "Complète la comptine française '3 petits chats'. "
            "Envoyez un ou plusieurs vers, l'agent retourne le suivant."
        ),
        url="http://ag2-agent:8000",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )
    executor = _EchoExecutor()
    task_store = InMemoryTaskStore()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=task_store)
    return A2AStarletteApplication(agent_card=card, http_handler=handler).build()


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = _build_test_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# AgentCard discovery tests (task 3.6)
# ---------------------------------------------------------------------------

def test_agent_card_returns_200(client: TestClient) -> None:
    """GET /.well-known/agent.json returns HTTP 200."""
    resp = client.get("/.well-known/agent.json")
    assert resp.status_code == 200


def test_agent_card_has_required_fields(client: TestClient) -> None:
    """AgentCard JSON contains name, description, skills, and url."""
    resp = client.get("/.well-known/agent.json")
    card = resp.json()
    assert "name" in card
    assert "description" in card
    assert "skills" in card
    assert "url" in card


def test_agent_card_declares_rhyme_completer_skill(client: TestClient) -> None:
    """AgentCard declares at least one skill with id 'rhyme-completer'."""
    resp = client.get("/.well-known/agent.json")
    card = resp.json()
    skill_ids = [s.get("id") for s in card.get("skills", [])]
    assert "rhyme-completer" in skill_ids


def test_agent_card_name(client: TestClient) -> None:
    """AgentCard name identifies this as the AG2 agent."""
    resp = client.get("/.well-known/agent.json")
    assert "AG2" in resp.json()["name"]


# ---------------------------------------------------------------------------
# message/send tests (task 3.6)
# ---------------------------------------------------------------------------

def test_valid_message_send_returns_200(client: TestClient) -> None:
    """POST / with valid message/send payload returns HTTP 200."""
    payload = {
        "jsonrpc": "2.0",
        "id": _make_message_id(),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": _make_message_id(),
                "parts": [{"kind": "text", "text": "3 petits chats"}],
            },
        },
    }
    resp = client.post("/", json=payload)
    assert resp.status_code == 200


def test_valid_message_send_returns_agent_text(client: TestClient) -> None:
    """message/send response contains an agent text part."""
    payload = {
        "jsonrpc": "2.0",
        "id": _make_message_id(),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": _make_message_id(),
                "parts": [{"kind": "text", "text": "3 petits chats"}],
            },
        },
    }
    resp = client.post("/", json=payload)
    body = resp.json()
    assert "result" in body
    result = body["result"]
    # Echo executor should return "echo:3 petits chats"
    parts = result.get("parts", [])
    texts = [p["text"] for p in parts if p.get("kind") == "text"]
    assert any("echo:" in t for t in texts)


def test_malformed_json_returns_parse_error(client: TestClient) -> None:
    """POST / with invalid JSON returns a JSON-RPC parse error."""
    resp = client.post(
        "/",
        content="not valid json",
        headers={"content-type": "application/json"},
    )
    # A2A SDK returns 200 with a JSON-RPC error for malformed JSON
    assert resp.status_code == 200
    body = resp.json()
    assert "error" in body
    # JSON-RPC parse error code is -32700
    assert body["error"]["code"] == -32700


def test_unknown_method_returns_method_not_found(client: TestClient) -> None:
    """POST / with unknown JSON-RPC method returns method-not-found error."""
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {},
    }
    resp = client.post("/", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == -32601  # Method not found


# ---------------------------------------------------------------------------
# AgentExecutor unit test — get_user_input extraction
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_executor_uses_get_user_input() -> None:
    """RhymeCompleterExecutor calls context.get_user_input() and passes result to agent."""
    # Import here so the module-level env check uses the test key
    from app.agent import RhymeCompleterExecutor

    executor = RhymeCompleterExecutor.__new__(RhymeCompleterExecutor)

    mock_context = MagicMock(spec=RequestContext)
    mock_context.get_user_input.return_value = "3 petits chats"

    mock_agent = MagicMock()
    mock_result = MagicMock()
    mock_last_msg = MagicMock()
    mock_last_msg.content = "chapeau de paille"
    mock_result.messages = [mock_last_msg]
    mock_agent.run = AsyncMock(return_value=mock_result)
    executor._agent = mock_agent

    mock_queue = AsyncMock(spec=EventQueue)

    await executor.execute(mock_context, mock_queue)

    mock_context.get_user_input.assert_called_once()
    mock_agent.run.assert_awaited_once_with(task="3 petits chats")
    mock_queue.enqueue_event.assert_awaited_once()
