from __future__ import annotations

import asyncio

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message

from app.crew import build_crew


class RhymeCompleterExecutor(AgentExecutor):
    """CrewAI Crew wrapped as an A2A AgentExecutor.

    CrewAI's kickoff() is synchronous, so we dispatch it to a thread pool
    to avoid blocking the async event loop.
    """

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_text = _extract_text(context)
        crew = build_crew(user_text)
        loop = asyncio.get_event_loop()
        # run_in_executor avoids blocking the uvicorn event loop
        result = await loop.run_in_executor(None, lambda: crew.kickoff())
        await event_queue.enqueue_event(new_agent_text_message(str(result)))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancel not supported")


def _extract_text(context: RequestContext) -> str:
    """Extract plain text from the first text part of the incoming A2A message."""
    try:
        parts = context.message.parts
        texts = [p.root.text for p in parts if hasattr(p, "root") and hasattr(p.root, "text")]
        return " ".join(texts) if texts else ""
    except AttributeError:
        return str(context.message)
