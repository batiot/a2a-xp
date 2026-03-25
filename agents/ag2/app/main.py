from __future__ import annotations

import os
import uvicorn

# NOTE: a2a-sdk import paths may vary by version.
# Verify with context7 before modifying.
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from app.agent import RhymeCompleterExecutor

# Fail fast on missing API key
_GOOGLE_STUDIO_API_KEY = os.environ["GOOGLE_STUDIO_API_KEY"]

AGENT_URL = os.environ.get("AGENT_URL", "http://ag2-agent:8000")

agent_card = AgentCard(
    name="Rhyme Completer (AG2)",
    description=(
        "Complète la comptine française '3 petits chats'. "
        "Envoyez un ou plusieurs vers, l'agent retourne le suivant."
    ),
    url=AGENT_URL,
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="rhyme-completer",
            name="Complete a rhyme",
            description="Given partial verses of '3 petits chats', returns the next verse.",
            tags=[],
            inputModes=["text"],
            outputModes=["text"],
        )
    ],
)


def build_app() -> object:
    executor = RhymeCompleterExecutor()
    task_store = InMemoryTaskStore()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=task_store)
    return A2AStarletteApplication(agent_card=agent_card, http_handler=handler).build()


app = build_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")
