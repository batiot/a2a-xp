from __future__ import annotations

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from langchain_core.messages import HumanMessage

from app.graph import graph


class RhymeCompleterExecutor(AgentExecutor):
    """LangGraph StateGraph wrapped as an A2A AgentExecutor.

    graph.ainvoke() is natively async, so no thread pool is needed.
    """

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_text = context.get_user_input()
        result = await graph.ainvoke({"messages": [HumanMessage(content=user_text)]})
        last_msg = result["messages"][-1]
        await event_queue.enqueue_event(new_agent_text_message(last_msg.content))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancel not supported")
