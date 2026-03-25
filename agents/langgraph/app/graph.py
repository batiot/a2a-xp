from __future__ import annotations

import os
from typing import Annotated

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# Fail fast on missing API key
_GOOGLE_STUDIO_API_KEY = os.environ["GOOGLE_STUDIO_API_KEY"]

SYSTEM_PROMPT = """Tu es un expert des comptines françaises pour enfants,
en particulier '3 petits chats'. Tu connais chaque vers par cœur.
Quand on te donne un ou plusieurs vers, tu réponds UNIQUEMENT avec le vers suivant.
Pas d'explication, pas de ponctuation supplémentaire."""


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    google_api_key=_GOOGLE_STUDIO_API_KEY,
    temperature=0,
)


def rhyme_node(state: State) -> dict:
    """Single LLM node: prepend system prompt and call the model."""
    from langchain_core.messages import SystemMessage

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


# Build the graph
builder = StateGraph(State)
builder.add_node("rhyme", rhyme_node)
builder.set_entry_point("rhyme")
builder.add_edge("rhyme", END)

# This `graph` name is referenced in langgraph.json
graph = builder.compile()
