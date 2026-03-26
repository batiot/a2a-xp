"""Tests for the A2A test client.

Validates observable behaviour:
- extract_result_text handles message/send responses correctly
- fetch_agent_card handles HTTP success and errors
- send_task sends the correct message/send JSON-RPC payload
"""
from __future__ import annotations

import os
import sys
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import extract_result_text, fetch_agent_card, send_task


# ---------------------------------------------------------------------------
# extract_result_text tests
# ---------------------------------------------------------------------------

def test_extract_result_text_from_message_response() -> None:
    """extract_result_text returns text from a message/send message result."""
    response = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
            "kind": "message",
            "messageId": "abc",
            "role": "agent",
            "parts": [{"kind": "text", "text": "chapeau de paille"}],
        },
    }
    assert extract_result_text(response) == "chapeau de paille"


def test_extract_result_text_none_response() -> None:
    """extract_result_text handles None gracefully."""
    assert extract_result_text(None) == "[no response]"


def test_extract_result_text_jsonrpc_error() -> None:
    """extract_result_text returns error description for JSON-RPC error responses."""
    response = {
        "jsonrpc": "2.0",
        "id": "1",
        "error": {"code": -32601, "message": "Method not found"},
    }
    result = extract_result_text(response)
    assert "[ERROR]" in result
    assert "Method not found" in result


def test_extract_result_text_empty_message_parts() -> None:
    """extract_result_text returns placeholder when message has no text parts."""
    response = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
            "kind": "message",
            "messageId": "abc",
            "role": "agent",
            "parts": [],
        },
    }
    assert extract_result_text(response) == "[empty message]"


def test_extract_result_text_task_failed() -> None:
    """extract_result_text returns failure description for failed task results."""
    response = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
            "kind": "task",
            "status": {"state": "failed", "error": {"message": "LLM timeout"}},
        },
    }
    result = extract_result_text(response)
    assert "[FAILED]" in result
    assert "LLM timeout" in result


def test_extract_result_text_empty_result() -> None:
    """extract_result_text returns placeholder for empty result."""
    assert extract_result_text({}) == "[empty result]"


# ---------------------------------------------------------------------------
# fetch_agent_card tests
# ---------------------------------------------------------------------------

def test_fetch_agent_card_success() -> None:
    """fetch_agent_card returns parsed JSON on HTTP 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "Test Agent",
        "skills": [{"id": "rhyme-completer"}],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        card = fetch_agent_card("http://localhost:8000")

    assert card is not None
    assert card["name"] == "Test Agent"


def test_fetch_agent_card_http_error_returns_none() -> None:
    """fetch_agent_card returns None when the agent is unreachable."""
    with patch("httpx.get", side_effect=httpx.ConnectError("connection refused")):
        card = fetch_agent_card("http://localhost:9999")
    assert card is None


def test_fetch_agent_card_warns_on_missing_skills(caplog: Any) -> None:
    """fetch_agent_card logs a warning when AgentCard is missing 'skills'."""
    import logging

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": "No Skills Agent"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        with caplog.at_level(logging.WARNING):
            card = fetch_agent_card("http://localhost:8000")

    assert card is not None
    assert any("skills" in msg.lower() for msg in caplog.messages)


# ---------------------------------------------------------------------------
# send_task tests
# ---------------------------------------------------------------------------

def test_send_task_uses_message_send_method() -> None:
    """send_task sends a message/send JSON-RPC request (not the old tasks/send)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
            "kind": "message",
            "messageId": "reply-1",
            "role": "agent",
            "parts": [{"kind": "text", "text": "chapeau de paille"}],
        },
    }

    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> MagicMock:
        captured["payload"] = kwargs.get("json", {})
        return mock_response

    with patch("httpx.post", side_effect=fake_post):
        result = send_task("http://localhost:8000", "3 petits chats")

    assert result is not None
    assert captured["payload"]["method"] == "message/send"


def test_send_task_payload_has_correct_structure() -> None:
    """send_task payload has messageId and kind:text part."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"jsonrpc": "2.0", "id": "1", "result": {}}

    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> MagicMock:
        captured["payload"] = kwargs.get("json", {})
        return mock_response

    with patch("httpx.post", side_effect=fake_post):
        send_task("http://localhost:8000", "3 petits chats")

    params = captured["payload"]["params"]
    message = params["message"]
    assert message["role"] == "user"
    assert "messageId" in message
    parts = message["parts"]
    assert any(p.get("kind") == "text" and p.get("text") == "3 petits chats" for p in parts)


def test_send_task_http_error_returns_none() -> None:
    """send_task returns None when the HTTP request fails."""
    with patch("httpx.post", side_effect=httpx.ConnectError("connection refused")):
        result = send_task("http://localhost:9999", "3 petits chats")
    assert result is None
