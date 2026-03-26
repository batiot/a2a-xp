from __future__ import annotations

import os
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from app.agent_executor import RhymeCompleterExecutor
from app.crew import get_agent_card

# Fail fast on missing API key
_GOOGLE_STUDIO_API_KEY = os.environ["GOOGLE_STUDIO_API_KEY"]

AGENT_URL = os.environ.get("AGENT_URL", "http://crewai-agent:8000")


def build_app() -> object:
    # AgentCard is generated natively by CrewAI from A2AServerConfig
    agent_card = get_agent_card(AGENT_URL)
    executor = RhymeCompleterExecutor()
    task_store = InMemoryTaskStore()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=task_store)
    return A2AStarletteApplication(agent_card=agent_card, http_handler=handler).build()


app = build_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")
