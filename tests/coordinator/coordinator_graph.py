"""Coordinateur LangGraph pour la comptine "Trois petits chats".

Orchestre les 3 agents A2A en round-robin (ag2 → crewai → langgraph → ag2 → ...)
pendant 9 tours au total (3 par agent), puis vérifie la séquence finale.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from tests.coordinator.verifier import RhymeVerifier

# ---------------------------------------------------------------------------
# Agent URLs — configurable via env vars
# ---------------------------------------------------------------------------
AGENT_ORDER = ["ag2", "crewai", "langgraph"]

TOTAL_TURNS = 9  # 3 agents × 3 tours chacun
INITIAL_VERSE = "Trois petits chats"


def _agent_urls() -> dict[str, str]:
    return {
        "ag2": os.environ.get("AG2_AGENT_URL", "http://localhost:10000"),
        "crewai": os.environ.get("CREWAI_AGENT_URL", "http://localhost:10001"),
        "langgraph": os.environ.get("LG_AGENT_URL", "http://localhost:10002"),
    }


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class CoordinatorState(TypedDict):
    sequence: list[str]           # vers accumulés (initial + réponses)
    turn: int                     # tour global courant (0 = avant le 1er appel)
    agent_counts: dict[str, int]  # nb d'appels par agent
    current_verse: str            # vers à envoyer au prochain agent
    verification: dict[str, Any]  # résultat du vérificateur final


# ---------------------------------------------------------------------------
# Helper: appel A2A JSON-RPC
# ---------------------------------------------------------------------------
async def _call_a2a_agent(url: str, verse: str) -> str:
    """Envoie un vers à un agent A2A et retourne le vers suivant.

    Handles two A2A response shapes:
    - message format (CrewAI, LangGraph): result.kind == "message" → result.parts[].text
    - task format (AG2):  result.kind == "task" → result.artifacts[n].parts[].text
    """
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": str(uuid.uuid4()),
                "parts": [{"kind": "text", "text": verse}],
            }
        },
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        body = resp.json()

    result = body.get("result", {})

    # Message format: parts directly on result
    for part in result.get("parts", []):
        if part.get("kind") == "text":
            return part["text"].strip()

    # Task format: parts nested inside artifacts
    for artifact in result.get("artifacts", []):
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                return part["text"].strip()

    raise ValueError(f"Aucun texte dans la réponse A2A de {url}: {body}")


# ---------------------------------------------------------------------------
# Routing function (used as conditional edge)
# ---------------------------------------------------------------------------
def route_node(state: CoordinatorState) -> str:
    """Détermine le prochain nœud : agent A2A ou vérificateur."""
    if state["turn"] >= TOTAL_TURNS:
        return "verify"
    agent_name = AGENT_ORDER[state["turn"] % len(AGENT_ORDER)]
    return f"call_{agent_name}"


# ---------------------------------------------------------------------------
# Agent call nodes (one per agent for explicit LangGraph routing)
# ---------------------------------------------------------------------------
async def call_ag2_node(state: CoordinatorState) -> dict:
    urls = _agent_urls()
    next_verse = await _call_a2a_agent(urls["ag2"], state["current_verse"])
    new_counts = dict(state["agent_counts"])
    new_counts["ag2"] = new_counts.get("ag2", 0) + 1
    return {
        "sequence": state["sequence"] + [next_verse],
        "turn": state["turn"] + 1,
        "agent_counts": new_counts,
        "current_verse": next_verse,
    }


async def call_crewai_node(state: CoordinatorState) -> dict:
    urls = _agent_urls()
    next_verse = await _call_a2a_agent(urls["crewai"], state["current_verse"])
    new_counts = dict(state["agent_counts"])
    new_counts["crewai"] = new_counts.get("crewai", 0) + 1
    return {
        "sequence": state["sequence"] + [next_verse],
        "turn": state["turn"] + 1,
        "agent_counts": new_counts,
        "current_verse": next_verse,
    }


async def call_langgraph_node(state: CoordinatorState) -> dict:
    urls = _agent_urls()
    next_verse = await _call_a2a_agent(urls["langgraph"], state["current_verse"])
    new_counts = dict(state["agent_counts"])
    new_counts["langgraph"] = new_counts.get("langgraph", 0) + 1
    return {
        "sequence": state["sequence"] + [next_verse],
        "turn": state["turn"] + 1,
        "agent_counts": new_counts,
        "current_verse": next_verse,
    }


async def verify_node(state: CoordinatorState) -> dict:
    """Appelle le vérificateur LLM sur la séquence complète."""
    verifier = RhymeVerifier()
    result = await verifier.verify(state["sequence"])
    return {"verification": result}


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------
_ROUTING_MAP = {
    "call_ag2": "call_ag2",
    "call_crewai": "call_crewai",
    "call_langgraph": "call_langgraph",
    "verify": "verify",
}

_builder = StateGraph(CoordinatorState)
_builder.add_node("call_ag2", call_ag2_node)
_builder.add_node("call_crewai", call_crewai_node)
_builder.add_node("call_langgraph", call_langgraph_node)
_builder.add_node("verify", verify_node)

_builder.add_conditional_edges(START, route_node, _ROUTING_MAP)
for _agent in AGENT_ORDER:
    _builder.add_conditional_edges(f"call_{_agent}", route_node, _ROUTING_MAP)
_builder.add_edge("verify", END)

graph = _builder.compile()


def initial_state() -> CoordinatorState:
    """Retourne l'état initial du coordinateur."""
    return CoordinatorState(
        sequence=[INITIAL_VERSE],
        turn=0,
        agent_counts={"ag2": 0, "crewai": 0, "langgraph": 0},
        current_verse=INITIAL_VERSE,
        verification={},
    )
