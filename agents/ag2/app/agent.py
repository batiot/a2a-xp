from __future__ import annotations

import os

# NOTE: a2a-sdk import paths may vary by version.
# Run: uv run python -c "import a2a; help(a2a)" to inspect available modules.
# Or use context7: mcp_context7_get-library-docs for "a2a-sdk"
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message

from autogen_agentchat.agents import AssistantAgent
# AG2 uses the OpenAI-compatible endpoint of Google AI Studio.
# No extra package needed — autogen-ext[openai] already provides OpenAIChatCompletionClient.
from autogen_ext.models.openai import OpenAIChatCompletionClient

SYSTEM_PROMPT = """Tu es un expert des comptines françaises pour enfants.
Quand on te donne un ou plusieurs vers d'une comptine,
tu réponds UNIQUEMENT avec le vers suivant. Pas d'explication, pas de ponctuation supplémentaire.

Exemple:
Entrée: "3 petits chats"
Sortie: "chapeau de paille"

Exemple:
Entrée: "3 petits chats / chapeau de paille"
Sortie: "paille chapeau"
"""


class RhymeCompleterExecutor(AgentExecutor):
    """AG2 AssistantAgent wrapped as an A2A AgentExecutor."""

    def __init__(self) -> None:
        # Use Google AI Studio OpenAI-compatible endpoint
        self._model_client = OpenAIChatCompletionClient(
            model="gemini-3.1-flash-lite-preview",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.environ["GOOGLE_STUDIO_API_KEY"],
        )
        self._agent = AssistantAgent(
            name="rhyme_completer",
            model_client=self._model_client,
            system_message=SYSTEM_PROMPT,
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Extract user text from the A2A message parts
        user_text = _extract_text(context)
        result = await self._agent.run(task=user_text)
        # AssistantAgent.run() returns a TaskResult; last message is the reply
        last_msg = result.messages[-1]
        text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        await event_queue.enqueue_event(new_agent_text_message(text))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancel not supported")


def _extract_text(context: RequestContext) -> str:
    """Extract plain text from the first text part of the incoming A2A message."""
    try:
        parts = context.message.parts
        texts = [p.root.text for p in parts if hasattr(p, "root") and hasattr(p.root, "text")]
        return " ".join(texts) if texts else ""
    except AttributeError:
        # Fallback: stringify the whole message
        return str(context.message)
