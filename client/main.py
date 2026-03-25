from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import httpx
from rich.console import Console
from rich.table import Table

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

console = Console()

# Agent URLs — default to Docker service names, overridable via env
AGENTS: dict[str, str] = {
    "AG2":       os.environ.get("AG2_URL",       "http://ag2-agent:8000"),
    "CrewAI":    os.environ.get("CREWAI_URL",    "http://crewai-agent:8000"),
    "LangGraph": os.environ.get("LANGGRAPH_URL", "http://langgraph-agent:8000"),
}

# The rhyme prompt sent to all three agents
RHYME_INPUT = "3 petits chats / qui mangeaient des rats"


def fetch_agent_card(base_url: str, timeout: float = 5.0) -> dict[str, Any] | None:
    """Fetch and validate the A2A AgentCard from /.well-known/agent.json."""
    url = f"{base_url}/.well-known/agent.json"
    try:
        resp = httpx.get(url, timeout=timeout)
        resp.raise_for_status()
        card = resp.json()
        if "skills" not in card:
            logger.warning("AgentCard at %s missing 'skills' field", url)
        return card
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch AgentCard from %s: %s", url, exc)
        return None


def send_task(base_url: str, user_text: str, timeout: float = 30.0) -> dict[str, Any] | None:
    """Send an A2A tasks/send JSON-RPC request and return the parsed response."""
    task_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "id": task_id,
        "method": "tasks/send",
        "params": {
            "id": task_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": user_text}],
            },
        },
    }
    try:
        resp = httpx.post(base_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        response = resp.json()
        result_id = response.get("result", {}).get("id", task_id)
        logger.info("A2A task submitted", extra={"task_id": result_id, "agent_url": base_url})
        return response
    except httpx.HTTPError as exc:
        logger.error("Failed to send task to %s: %s", base_url, exc)
        return None


def extract_result_text(response: dict[str, Any] | None) -> str:
    """Pull the text result from an A2A tasks/send response."""
    if response is None:
        return "[no response]"

    result = response.get("result", {})

    # Check for task failure
    state = result.get("status", {}).get("state", "")
    if state == "failed":
        error = result.get("status", {}).get("error", {})
        return f"[FAILED] {error.get('message', 'unknown error')}"

    # Try to extract text from artifacts
    artifacts = result.get("artifacts", [])
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if part.get("type") == "text":
                return part["text"]

    # Fallback: stringify the whole result
    return str(result) if result else "[empty result]"


def main() -> None:
    console.rule("[bold blue]A2A Multiframework Lab — Test Client[/bold blue]")
    console.print(f"\n[bold]Rhyme input:[/bold] {RHYME_INPUT!r}\n")

    # --- Step 1: Discover all AgentCards ---
    console.rule("AgentCard Discovery")
    cards_table = Table("Agent", "Name", "Skills", show_lines=True)
    available: dict[str, str] = {}

    for name, url in AGENTS.items():
        card = fetch_agent_card(url)
        if card:
            skill_names = ", ".join(s.get("id", "?") for s in card.get("skills", []))
            cards_table.add_row(name, card.get("name", "?"), skill_names)
            available[name] = url
        else:
            cards_table.add_row(name, "[red]unreachable[/red]", "—")

    console.print(cards_table)

    if not available:
        console.print("\n[red]No agents available. Start at least one agent first.[/red]")
        return

    # --- Step 2: Send rhyme prompt to each available agent ---
    console.rule("Task Results")
    results_table = Table("Agent", "Response", show_lines=True, expand=True)

    for name, url in available.items():
        response = send_task(url, RHYME_INPUT)
        text = extract_result_text(response)
        results_table.add_row(name, text)

    console.print(results_table)
    console.rule("[green]Done[/green]")


if __name__ == "__main__":
    main()
