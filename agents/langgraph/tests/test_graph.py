"""Tests for the LangGraph rhyme-completer graph.

These tests validate the graph structure and node logic without hitting
the LangGraph Agent Server or a real LLM. The Google API call is mocked.

Task 5.6 coverage: verifies the graph is compilable and the rhyme node
correctly prepends the system prompt and returns a model response.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure the agent package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Provide a dummy API key so module-level env checks pass
os.environ.setdefault("GOOGLE_STUDIO_API_KEY", "test-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-key")


# ---------------------------------------------------------------------------
# Graph structure tests (task 5.6)
# ---------------------------------------------------------------------------

def test_graph_compiles_without_error() -> None:
    """The StateGraph compiles to a runnable graph without error."""
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        # Re-import to pick up the mock (graph is compiled at module level)
        import importlib
        import app.graph as graph_module
        importlib.reload(graph_module)
        assert graph_module.graph is not None


def test_graph_has_rhyme_node() -> None:
    """The compiled graph contains a 'rhyme' node."""
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm_cls.return_value = MagicMock()
        import importlib
        import app.graph as graph_module
        importlib.reload(graph_module)
        # langgraph compiled graphs expose nodes via .nodes or graph structure
        assert "rhyme" in graph_module.builder.nodes


def test_rhyme_node_prepends_system_prompt() -> None:
    """rhyme_node prepends the SYSTEM_PROMPT as a SystemMessage before the user messages."""
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="chapeau de paille")
        mock_llm_cls.return_value = mock_llm
        import importlib
        import app.graph as graph_module
        importlib.reload(graph_module)

        from langchain_core.messages import HumanMessage, SystemMessage

        state = {"messages": [HumanMessage(content="3 petits chats")]}
        result = graph_module.rhyme_node(state)

        # The LLM should have been called with system + user messages
        call_args = mock_llm.invoke.call_args[0][0]
        assert isinstance(call_args[0], SystemMessage)
        assert call_args[0].content == graph_module.SYSTEM_PROMPT
        assert call_args[1].content == "3 petits chats"

        # The result dict should have a messages key
        assert "messages" in result
        assert len(result["messages"]) == 1


def test_rhyme_node_returns_model_response() -> None:
    """rhyme_node returns the model's response in the messages list."""
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_response = MagicMock()
        mock_response.content = "chapeau de paille"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        mock_llm_cls.return_value = mock_llm
        import importlib
        import app.graph as graph_module
        importlib.reload(graph_module)

        from langchain_core.messages import HumanMessage

        state = {"messages": [HumanMessage(content="3 petits chats")]}
        result = graph_module.rhyme_node(state)

        assert result["messages"][0] is mock_response


def test_langgraph_json_points_to_graph() -> None:
    """langgraph.json descriptor references the correct graph entrypoint."""
    import json
    descriptor_path = os.path.join(
        os.path.dirname(__file__), "..", "langgraph.json"
    )
    with open(descriptor_path) as f:
        descriptor = json.load(f)

    graphs = descriptor.get("graphs", {})
    assert "rhyme_completer" in graphs
    assert "graph.py:graph" in graphs["rhyme_completer"]
