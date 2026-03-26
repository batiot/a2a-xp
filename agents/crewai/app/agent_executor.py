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
        user_text = context.get_user_input()
        crew = build_crew(user_text)
        loop = asyncio.get_running_loop()
        # run_in_executor avoids blocking the uvicorn event loop
        result = await loop.run_in_executor(None, lambda: crew.kickoff())
        await event_queue.enqueue_event(new_agent_text_message(str(result)))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancel not supported")
